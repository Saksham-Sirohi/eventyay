import logging

from django.conf import settings
from django.core import cache
from django.http import HttpResponse

from eventyay.base.operational_logging import OUTCOME_FAILURE, log_event

from ..models import User

logger = logging.getLogger(__name__)


def healthcheck(request):
    # Perform a simple DB query to see that DB access works
    User.objects.exists()

    # Test if redis access works
    if settings.HAS_REDIS:
        import django_redis

        redis = django_redis.get_redis_connection('redis')
        redis.set('_healthcheck', 1)
        if not redis.exists('_healthcheck'):
            log_event('core', 'health.check', OUTCOME_FAILURE, error_code='redis_unavailable')
            logger.error('Health check failed: redis unavailable')
            return HttpResponse('Redis not available.', status=503)

    cache.cache.set('_healthcheck', '1')
    if not cache.cache.get('_healthcheck') == '1':
        log_event('core', 'health.check', OUTCOME_FAILURE, error_code='cache_unavailable')
        logger.error('Health check failed: cache unavailable')
        return HttpResponse('Cache not available.', status=503)

    return HttpResponse()
