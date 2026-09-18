from eventyay.base.pdf import apply_layout_flow, drop_line_emptied_by_placeholder
from eventyay.plugins.badges.models import BadgeLayout


def _textarea(**kwargs):
    obj = {
        'type': 'textarea',
        'left': '0',
        'bottom': '80',
        'fontsize': '10.0',
        'width': '40',
        'fontfamily': 'Open Sans',
        'bold': False,
        'italic': False,
        'align': 'center',
        'color': [0, 0, 0, 1],
        'flow_group': 'attendee-text',
        'flow_direction': 'down',
        'flow_adopt_slot_style': True,
        'autofit_width': True,
        'content': 'field',
        'text': 'Sample',
    }
    obj.update(kwargs)
    return obj


def _empty_contents(hidden):
    hidden = set(hidden)

    def is_empty(obj):
        return obj.get('content') in hidden

    return is_empty


def test_stacked_ungrouped_fields_compact_without_adopting_style():
    layout = [
        _textarea(content='attendee_name', flow_group='', bottom='85', fontsize='16.0', width='80'),
        _textarea(content='home_wiki', flow_group='', bottom='70', fontsize='10.0', width='40'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_name']))
    assert len(packed) == 1
    assert packed[0]['content'] == 'home_wiki'
    assert packed[0]['bottom'] == '85'
    assert packed[0]['fontsize'] == '10.0'
    assert packed[0]['width'] == '40'


def test_distant_ungrouped_fields_are_not_packed():
    layout = [
        _textarea(content='attendee_name', flow_group='', bottom='85', fontsize='16.0'),
        _textarea(content='event_name', flow_group='', bottom='14', fontsize='12.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_name']))
    assert packed[0]['content'] == 'attendee_name'
    assert packed[1]['content'] == 'event_name'
    assert packed[1]['bottom'] == '14'


def test_legal_name_and_home_wiki_have_no_blank_gap():
    layout = [
        _textarea(content='attendee_name', flow_group='', bottom='85', fontsize='16.0'),
        _textarea(content='attendee_job_title', flow_group='', bottom='76', fontsize='12.0'),
        _textarea(content='home_wiki', flow_group='', bottom='64', fontsize='10.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_job_title']))
    assert [obj['content'] for obj in packed] == ['attendee_name', 'home_wiki']
    assert packed[0]['bottom'] == '85'
    assert packed[1]['bottom'] == '76'


def test_placeholder_blank_lines_are_removed_when_fields_are_empty():
    assert drop_line_emptied_by_placeholder('{home_wiki}', '', True) is True
    assert drop_line_emptied_by_placeholder('', '', False) is False
    assert drop_line_emptied_by_placeholder('{attendee_name}', 'Ada Lovelace', True) is False


def test_all_visible_ungrouped_stacked_fields_keep_slots():
    layout = [
        _textarea(content='attendee_name', flow_group='', bottom='85', fontsize='16.0'),
        _textarea(content='home_wiki', flow_group='', bottom='70', fontsize='10.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents([]))
    assert [obj['content'] for obj in packed] == ['attendee_name', 'home_wiki']
    assert packed[0]['bottom'] == '85'
    assert packed[1]['bottom'] == '70'


def test_hidden_field_promotes_next_into_first_slot_with_style():
    layout = [
        _textarea(content='attendee_name', bottom='85', fontsize='16.0', bold=True, width='80'),
        _textarea(content='attendee_company', bottom='70', fontsize='10.0', bold=False, width='40'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_name']))
    assert len(packed) == 1
    assert packed[0]['content'] == 'attendee_company'
    assert packed[0]['bottom'] == '85'
    assert packed[0]['fontsize'] == '16.0'
    assert packed[0]['bold'] is True
    assert packed[0]['width'] == '80'


def test_adopt_slot_style_can_be_disabled():
    layout = [
        _textarea(
            content='attendee_name',
            bottom='85',
            fontsize='16.0',
            width='80',
            flow_adopt_slot_style=False,
        ),
        _textarea(
            content='attendee_company',
            bottom='70',
            fontsize='10.0',
            width='40',
            flow_adopt_slot_style=False,
        ),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_name']))
    assert packed[0]['content'] == 'attendee_company'
    assert packed[0]['bottom'] == '85'
    assert packed[0]['fontsize'] == '10.0'
    assert packed[0]['width'] == '40'


def test_all_visible_fields_keep_order_and_slots():
    layout = [
        _textarea(content='attendee_name', bottom='85', fontsize='16.0'),
        _textarea(content='attendee_company', bottom='70', fontsize='10.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents([]))
    assert [obj['content'] for obj in packed] == ['attendee_name', 'attendee_company']
    assert packed[0]['bottom'] == '85'
    assert packed[1]['bottom'] == '70'


def test_single_visible_field_uses_first_slot():
    layout = [
        _textarea(content='attendee_name', bottom='85', fontsize='16.0'),
        _textarea(content='job', bottom='76', fontsize='12.0'),
        _textarea(content='wiki', bottom='64', fontsize='8.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_name', 'job']))
    assert len(packed) == 1
    assert packed[0]['content'] == 'wiki'
    assert packed[0]['bottom'] == '85'
    assert packed[0]['fontsize'] == '16.0'


def test_middle_hidden_field_promotes_later_field():
    layout = [
        _textarea(content='attendee_name', bottom='85', fontsize='16.0'),
        _textarea(content='job', bottom='76', fontsize='12.0'),
        _textarea(content='wiki', bottom='64', fontsize='8.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['job']))
    assert [obj['content'] for obj in packed] == ['attendee_name', 'wiki']
    assert packed[0]['bottom'] == '85'
    assert packed[1]['bottom'] == '76'
    assert packed[1]['fontsize'] == '12.0'


def test_locked_object_does_not_move():
    layout = [
        _textarea(content='attendee_name', bottom='85', fontsize='16.0'),
        {
            'type': 'barcodearea',
            'left': '20',
            'bottom': '30',
            'size': '25',
            'content': 'secret',
            'flow_group': 'attendee-text',
            'flow_lock': True,
            'flow_direction': 'down',
        },
        _textarea(content='attendee_company', bottom='70', fontsize='10.0'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['attendee_name']))
    barcode = next(obj for obj in packed if obj['type'] == 'barcodearea')
    company = next(obj for obj in packed if obj.get('content') == 'attendee_company')
    assert barcode['bottom'] == '30'
    assert company['bottom'] == '85'


def test_larger_skipped_slot_is_used_as_destination():
    layout = [
        _textarea(content='title', bottom='90', fontsize='24.0', width='100'),
        _textarea(content='subtitle', bottom='70', fontsize='8.0', width='50'),
    ]
    packed = apply_layout_flow(layout, _empty_contents(['title']))
    assert packed[0]['fontsize'] == '24.0'
    assert packed[0]['width'] == '100'


def test_default_badge_layout_includes_flow_group():
    layout = BadgeLayout().layout_data
    text = [obj for obj in layout if obj['type'] == 'textarea']
    assert {obj['content'] for obj in text} == {'attendee_name', 'attendee_job_title', 'attendee_company'}
    assert all(obj.get('flow_group') == 'attendee-text' for obj in text)
    assert all(obj.get('autofit_width') is True for obj in text)
    assert all(obj.get('flow_adopt_slot_style') is True for obj in text)


def test_default_badge_layout_compacts_unselected_fields():
    packed = apply_layout_flow(BadgeLayout().layout_data, _empty_contents(['attendee_job_title']))
    text = [obj for obj in packed if obj['type'] == 'textarea']
    assert [obj['content'] for obj in text] == ['attendee_name', 'attendee_company']
    assert text[0]['bottom'] == '85'
    assert text[1]['bottom'] == '83'
    barcode = next(obj for obj in packed if obj['type'] == 'barcodearea')
    assert barcode['bottom'] == '34'
