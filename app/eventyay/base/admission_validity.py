from datetime import timedelta
from types import SimpleNamespace

from django.utils.formats import date_format
from django.utils.timezone import now as timezone_now

from eventyay.base.models.product import Product, ProductVariation


def _pick_attr(variation, product, attr):
    value = getattr(variation, attr)
    if value is not None:
        return value
    return getattr(product, attr)


def _merged_catalog_config(product, variation=None):
    """
    Merge product and variation admission settings.

    Variation mode ``inherit`` (default) keeps the product mode and overlays only
    explicitly set variation fields. Any other variation mode replaces the product
    mode entirely, including ``''`` for an explicit "no restriction" override.
    """
    if variation is None:
        return product

    var_mode = variation.admission_validity_mode
    if var_mode == ProductVariation.ADMISSION_VALIDITY_MODE_INHERIT:
        mode = product.admission_validity_mode or ''
    else:
        mode = var_mode or ''

    if mode in ('', Product.ADMISSION_VALIDITY_MODE_NONE):
        return SimpleNamespace(
            admission_validity_mode=Product.ADMISSION_VALIDITY_MODE_NONE,
            admission_valid_from=None,
            admission_valid_until=None,
            admission_valid_from_offset_minutes=None,
            admission_valid_until_offset_minutes=None,
        )

    return SimpleNamespace(
        admission_validity_mode=mode,
        admission_valid_from=_pick_attr(variation, product, 'admission_valid_from'),
        admission_valid_until=_pick_attr(variation, product, 'admission_valid_until'),
        admission_valid_from_offset_minutes=_pick_attr(
            variation, product, 'admission_valid_from_offset_minutes'
        ),
        admission_valid_until_offset_minutes=_pick_attr(
            variation, product, 'admission_valid_until_offset_minutes'
        ),
    )


def _effective_mode(source):
    mode = source.admission_validity_mode or ''
    if mode == ProductVariation.ADMISSION_VALIDITY_MODE_INHERIT:
        return Product.ADMISSION_VALIDITY_MODE_NONE
    if not mode and (source.admission_valid_from or source.admission_valid_until):
        return Product.ADMISSION_VALIDITY_MODE_FIXED
    return mode


def _validity_window(event, subevent, mode):
    if mode == Product.ADMISSION_VALIDITY_MODE_EVENT:
        return event.date_from, event.date_to
    if mode == Product.ADMISSION_VALIDITY_MODE_SUBEVENT:
        if subevent is None:
            return None, None
        return subevent.date_from, subevent.date_to
    return None, None


def _apply_minute_offsets(window_start, window_end, offset_from, offset_until):
    if window_start is None:
        return None, None
    valid_from = window_start
    if offset_from is not None:
        valid_from = window_start + timedelta(minutes=offset_from)
    if offset_until is not None:
        valid_until = window_start + timedelta(minutes=offset_until)
    elif window_end:
        valid_until = window_end
    else:
        valid_until = None

    # Keep resolved windows inside the underlying event/date range.
    if window_start and valid_from and valid_from < window_start:
        valid_from = window_start
    if window_end and valid_until and valid_until > window_end:
        valid_until = window_end
    return valid_from, valid_until


def resolve_catalog_admission_bounds(product, variation=None, event=None, subevent=None):
    """
    Resolve the configured check-in window from product catalog data.

    Variation settings are merged field-by-field with the product. Fixed windows use
    explicit datetimes; subevent/event modes derive bounds from the assigned date or
    whole event, optionally shifted by minute offsets.
    """
    source = _merged_catalog_config(product, variation)
    mode = _effective_mode(source)
    if mode in ('', Product.ADMISSION_VALIDITY_MODE_NONE):
        return None, None
    if mode == Product.ADMISSION_VALIDITY_MODE_FIXED:
        return source.admission_valid_from, source.admission_valid_until
    if event is None:
        return None, None
    window_start, window_end = _validity_window(event, subevent, mode)
    return _apply_minute_offsets(
        window_start,
        window_end,
        source.admission_valid_from_offset_minutes,
        source.admission_valid_until_offset_minutes,
    )


def assign_issued_admission_bounds(position):
    """
    Copy the resolved check-in window onto an order position at purchase time.

    The stored values define check-in enforcement for this ticket even if the
    product is edited later. Both fields ``None`` means unrestricted at issue time.
    """
    if position.product_id is None and getattr(position, 'product', None) is None:
        return
    order = getattr(position, 'order', None)
    if order is None:
        return
    valid_from, valid_until = resolve_catalog_admission_bounds(
        position.product,
        position.variation,
        event=order.event,
        subevent=position.subevent,
    )
    position.admission_valid_from = valid_from
    position.admission_valid_until = valid_until


def get_issued_admission_bounds(position):
    """
    Effective check-in window for a sold ticket.

    Uses only the purchase-time snapshot on the position. Positions created before
    this feature (or issued with no restriction) have both fields ``None`` and are
    unrestricted; catalog configuration is never re-resolved for issued tickets.
    """
    return position.admission_valid_from, position.admission_valid_until


def is_within_admission_bounds(valid_from, valid_until, dt):
    if valid_from and dt < valid_from:
        return False
    if valid_until and dt > valid_until:
        return False
    return True


def is_catalog_admission_currently_valid(product, variation=None, event=None, subevent=None, dt=None):
    valid_from, valid_until = resolve_catalog_admission_bounds(product, variation, event, subevent)
    if not valid_from and not valid_until:
        return True
    dt = dt or timezone_now()
    return is_within_admission_bounds(valid_from, valid_until, dt)


def is_product_catalog_admission_orderable(product, event=None, subevent=None, dt=None):
    if not product.has_variations:
        return is_catalog_admission_currently_valid(product, None, event, subevent, dt)
    return any(
        is_catalog_admission_currently_valid(product, variation, event, subevent, dt)
        for variation in product.variations.all()
        if variation.active
    )


def has_issued_admission_bounds(position):
    valid_from, valid_until = get_issued_admission_bounds(position)
    return bool(valid_from or valid_until)


def format_admission_window(valid_from, valid_until, tz=None):
    if not valid_from and not valid_until:
        return ''

    def _fmt(dt):
        if dt is None:
            return ''
        if tz is not None:
            dt = dt.astimezone(tz)
        return date_format(dt, 'SHORT_DATETIME_FORMAT')

    if valid_from and valid_until:
        return f'{_fmt(valid_from)} – {_fmt(valid_until)}'
    if valid_from:
        return _fmt(valid_from)
    return _fmt(valid_until)


def format_catalog_admission_validity(product, event, subevent=None, variation=None, *, fallback_to_event=False):
    valid_from, valid_until = resolve_catalog_admission_bounds(
        product, variation=variation, event=event, subevent=subevent
    )
    if valid_from or valid_until:
        return format_admission_window(valid_from, valid_until, event.tz)
    if not fallback_to_event:
        return ''
    source = subevent or event
    return format_admission_window(source.date_from, source.date_to, event.tz)


def format_issued_admission_validity(position, event, *, fallback_to_event=False):
    valid_from, valid_until = get_issued_admission_bounds(position)
    if valid_from or valid_until:
        return format_admission_window(valid_from, valid_until, event.tz)
    if not fallback_to_event:
        return ''
    source = position.subevent or event
    return format_admission_window(source.date_from, source.date_to, event.tz)
