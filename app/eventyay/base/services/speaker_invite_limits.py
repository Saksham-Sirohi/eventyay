import logging
from datetime import UTC, datetime

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)

CFP_MAX_INVITE_SENDS_PER_HOUR = getattr(settings, 'CFP_MAX_INVITE_SENDS_PER_HOUR', 20)
CFP_MAX_INVITE_RESENDS = getattr(settings, 'CFP_MAX_INVITE_RESENDS', 3)


def get_invitation_resend_key(invitation_pk):
    return f'cfp_invite_resend_count:{invitation_pk}'


def get_invitation_resend_count(invitation_pk):
    if not invitation_pk:
        return 0
    try:
        return int(cache.get(get_invitation_resend_key(invitation_pk), 0) or 0)
    except Exception:
        return 0


def record_invitation_resend(invitation_pk):
    if not invitation_pk:
        return None
    key = get_invitation_resend_key(invitation_pk)
    timeout = 90 * 86400  # 90 days
    try:
        if cache.add(key, 1, timeout=timeout):
            return 1
        return cache.incr(key)
    except Exception:
        logger.exception('Could not increment invitation resend count for %s', invitation_pk)
        return None


def get_user_rate_limit_key(user_id, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(UTC)
    hour_bucket = timestamp.strftime('%Y%m%d%H')
    return f'cfp_invite_sends:{user_id}:{hour_bucket}'


def check_speaker_invite_rate_limit(user, limit=None):
    """Checks whether the user is within their hourly CfP invitation send budget."""
    if not user or not getattr(user, 'pk', None) or not getattr(user, 'is_authenticated', False):
        return True
    if getattr(user, 'is_administrator', False):
        return True

    limit = limit if limit is not None else CFP_MAX_INVITE_SENDS_PER_HOUR
    key = get_user_rate_limit_key(user.pk)
    try:
        current_count = int(cache.get(key, 0) or 0)
    except Exception:
        logger.exception('Could not read speaker invite rate limit for user %s; failing closed', user.pk)
        return False
    return current_count < limit


def check_and_record_speaker_invite_send(user, amount=1, limit=None):
    """Atomically increments the user's hourly send counter and checks the limit.

    Fails closed if the cache backend is unavailable.
    """
    if not user or not getattr(user, 'pk', None) or not getattr(user, 'is_authenticated', False):
        return True
    if getattr(user, 'is_administrator', False):
        return True

    limit = limit if limit is not None else CFP_MAX_INVITE_SENDS_PER_HOUR
    key = get_user_rate_limit_key(user.pk)
    timeout = 7200  # 2 hours

    try:
        if cache.add(key, amount, timeout=timeout):
            return amount <= limit
        new_count = cache.incr(key, amount)
        return new_count <= limit
    except Exception:
        logger.exception('Could not record speaker invite rate limit for user %s; failing closed', user.pk)
        return False
