from django.apps import AppConfig


class EventyayBaseConfig(AppConfig):
    name = 'eventyay.base'
    label = 'base'

    def ready(self):
        from .operational_logging import connect_operational_signals

        connect_operational_signals()
        from . import exporter  # NOQA
        from . import payment  # NOQA
        from . import exporters  # NOQA
        from . import invoice  # NOQA
        from . import notifications  # NOQA
        from . import email  # NOQA
        from django.conf import settings

        try:
            from eventyay.celery_app import app as celery_app  # NOQA
        except ImportError:
            pass

        if hasattr(settings, 'RAVEN_CONFIG'):
            from eventyay.config.sentry import initialize

            initialize()


default_app_config = 'eventyay.base.EventyayBaseConfig'
try:
    import eventyay.celery_app as celery  # NOQA
except ImportError:
    pass
