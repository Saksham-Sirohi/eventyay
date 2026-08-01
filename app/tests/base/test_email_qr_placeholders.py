"""Tests for order QR and PDF download email placeholders."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from eventyay.base.email import (
    SimpleFunctionalMailTextPlaceholder,
    download_tickets_button_label,
    get_combined_ticket_output_identifier,
    render_download_tickets_pdf_button,
    render_order_qr_html,
    render_qr_code_img,
    render_ticket_qr_html,
)
from eventyay.base.templatetags.rich_text import (
    build_email_preview_context,
    is_placeholder_html_sample,
    markdown_compile_email,
)


def test_render_qr_code_img_uses_data_uri():
    html = render_qr_code_img('{"ticket":"secret"}', alt='Ticket QR code')
    assert html.startswith('<img src="data:image/png;base64,')
    assert 'alt="Ticket QR code"' in html
    assert 'width="160"' in html
    assert 'height="160"' in html


def test_render_qr_code_img_escapes_alt():
    html = render_qr_code_img('payload', alt='"><script>alert(1)</script>')
    assert '<script>' not in html
    assert '&lt;script&gt;' in html


def test_markdown_compile_email_preserves_qr_img():
    html = render_qr_code_img('ticket-secret', alt='Ticket QR code')
    compiled = markdown_compile_email(f'Scan this:\n\n{html}')
    assert 'data:image/png;base64,' in compiled
    assert '<img ' in compiled


def test_markdown_compile_email_strips_data_href_on_anchors():
    compiled = markdown_compile_email(
        '<a href="data:text/html,<script>alert(1)</script>" class="button">Click</a>'
    )
    assert 'data:text/html' not in compiled
    assert 'href=' not in compiled or 'href="data:' not in compiled


def test_render_ticket_qr_html(monkeypatch):
    position = SimpleNamespace(ticket_qrcode_content='{"event":"demo","ticket":"abc"}')
    html = render_ticket_qr_html(position)
    assert 'data:image/png;base64,' in html


def test_render_order_qr_html_skips_non_ticket_positions():
    ticket_pos = SimpleNamespace(
        generate_ticket=True,
        attendee_name='Ada Lovelace',
        product=SimpleNamespace(name='General'),
        ticket_qrcode_content='{"ticket":"one"}',
        positionid=1,
    )
    addon_pos = SimpleNamespace(
        generate_ticket=False,
        attendee_name=None,
        product=SimpleNamespace(name='T-Shirt'),
        ticket_qrcode_content='{"ticket":"two"}',
        positionid=2,
    )
    qs = MagicMock()
    qs.select_related.return_value.order_by.return_value = [ticket_pos, addon_pos]
    order = SimpleNamespace(positions=qs)

    html = render_order_qr_html(order)
    assert 'Ada Lovelace' in html
    assert 'T-Shirt' not in html
    assert html.count('<img ') == 1


def test_render_download_tickets_pdf_button(monkeypatch):
    event = MagicMock()
    order = SimpleNamespace(code='ABCDE', secret='secret-value')

    monkeypatch.setattr(
        'eventyay.base.email.get_combined_ticket_output_identifier',
        lambda event: 'pdf',
    )
    monkeypatch.setattr(
        'eventyay.multidomain.urlreverse.build_absolute_uri',
        lambda event, viewname, kwargs=None: (
            f'https://shop.example/{kwargs["order"]}/{kwargs["secret"]}/{kwargs["output"]}/?x=1&y=2'
        ),
    )

    html = render_download_tickets_pdf_button(event, order)
    assert 'class="button"' in html
    assert 'href="https://shop.example/ABCDE/secret-value/pdf/?x=1&amp;y=2"' in html
    assert 'Download tickets (PDF)' in html
    compiled = markdown_compile_email(html)
    assert 'class="button"' in compiled
    assert 'https://shop.example/ABCDE/secret-value/pdf/' in compiled


def test_render_download_tickets_button_non_pdf_label(monkeypatch):
    event = MagicMock()
    order = SimpleNamespace(code='ABCDE', secret='secret-value')

    monkeypatch.setattr(
        'eventyay.base.email.get_combined_ticket_output_identifier',
        lambda event: 'applepass',
    )
    monkeypatch.setattr(
        'eventyay.multidomain.urlreverse.build_absolute_uri',
        lambda event, viewname, kwargs=None: (
            f'https://shop.example/{kwargs["order"]}/{kwargs["secret"]}/{kwargs["output"]}/'
        ),
    )

    html = render_download_tickets_pdf_button(event, order)
    assert 'Download tickets (PDF)' not in html
    assert download_tickets_button_label('applepass') in html
    assert 'applepass' in html


def test_order_only_context_resolves_ticket_and_order_qr():
    """Buyer/order emails have order but no position; QR placeholders must still expand."""
    from i18nfield.strings import LazyI18nString

    from eventyay.base.services.mail import TolerantDict, render_mail

    order = SimpleNamespace()
    qs = MagicMock()
    ticket_pos = SimpleNamespace(
        generate_ticket=True,
        attendee_name='Ada',
        product=SimpleNamespace(name='General'),
        ticket_qrcode_content='{"ticket":"one"}',
        positionid=1,
    )
    qs.select_related.return_value.order_by.return_value = [ticket_pos]
    order.positions = qs

    template = 'Ticket: {ticket_qr}\n\nOrder: {order_qr}'
    ctx = {
        'ticket_qr': render_order_qr_html(order),
        'order_qr': render_order_qr_html(order),
    }
    body = render_mail(LazyI18nString(template), ctx)
    assert '{ticket_qr}' not in body
    assert '{order_qr}' not in body
    assert 'data:image/png;base64,' in body
    assert body == template.format_map(TolerantDict({k: str(v) for k, v in ctx.items()}))
    assert 'data:image/png;base64,' in markdown_compile_email(body)


def test_is_placeholder_html_sample_detects_qr_and_button():
    assert is_placeholder_html_sample('<img src="data:image/png;base64,abc" alt="QR">')
    assert is_placeholder_html_sample('<a href="https://example.com" class="button">Download</a>')
    assert is_placeholder_html_sample('<p><strong>Ada</strong></p><img src="data:image/png;base64,abc">')
    assert not is_placeholder_html_sample('F8VVL')
    assert not is_placeholder_html_sample('https://example.com/order')


def test_get_combined_ticket_output_identifier_prefers_pdf():
    event = MagicMock()

    class PdfProvider:
        identifier = 'pdf'
        is_enabled = True

    class OtherProvider:
        identifier = 'applepass'
        is_enabled = True

    with patch('eventyay.base.signals.register_ticket_outputs.send') as send:
        send.return_value = [
            (None, lambda e: OtherProvider()),
            (None, lambda e: PdfProvider()),
        ]
        assert get_combined_ticket_output_identifier(event) == 'pdf'


def test_get_combined_ticket_output_identifier_falls_back_to_first_enabled():
    event = MagicMock()

    class OtherProvider:
        identifier = 'applepass'
        is_enabled = True

    class DisabledPdf:
        identifier = 'pdf'
        is_enabled = False

    with patch('eventyay.base.signals.register_ticket_outputs.send') as send:
        send.return_value = [
            (None, lambda e: DisabledPdf()),
            (None, lambda e: OtherProvider()),
        ]
        assert get_combined_ticket_output_identifier(event) == 'applepass'


def test_build_email_preview_context_keeps_html_samples():
    event = MagicMock()
    qr_sample = render_qr_code_img('secret', alt='Ticket QR code')
    button_sample = '<a href="https://example.com" class="button">Download tickets (PDF)</a>'
    placeholders = {
        'code': SimpleFunctionalMailTextPlaceholder('code', ['order'], lambda order: order.code, 'F8VVL'),
        'ticket_qr': SimpleFunctionalMailTextPlaceholder(
            'ticket_qr', ['order'], lambda order: qr_sample, qr_sample
        ),
        'download_tickets_pdf': SimpleFunctionalMailTextPlaceholder(
            'download_tickets_pdf',
            ['order', 'event'],
            lambda order, event: button_sample,
            button_sample,
        ),
    }

    with patch(
        'eventyay.base.email.get_available_placeholders',
        return_value=placeholders,
    ):
        ctx = build_email_preview_context(event, ['event', 'order'])

    assert ctx['ticket_qr'] == qr_sample
    assert ctx['download_tickets_pdf'] == button_sample
    assert 'placeholder' in ctx['code']
    assert 'F8VVL' in ctx['code']
    assert '<span' in ctx['code']
