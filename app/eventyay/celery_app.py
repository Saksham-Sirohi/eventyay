import logging
import os

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun

os.environ.setdefault('EVY_RUNNING_ENVIRONMENT', 'development')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventyay.config.settings')

from django.conf import settings

logger = logging.getLogger(__name__)

app = Celery('eventyay')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@task_prerun.connect(weak=False)
def bind_operational_job_id(sender=None, task_id=None, **kwargs):
    from eventyay.base.operational_logging import bind_job_id

    if task_id:
        bind_job_id(task_id)


@task_postrun.connect(weak=False)
def reset_operational_job_id(sender=None, **kwargs):
    from eventyay.base.operational_logging import reset_job_id

    reset_job_id()


@task_failure.connect(weak=False)
def log_operational_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    from eventyay.base.operational_logging import OUTCOME_FAILURE, log_event

    job_name = getattr(sender, 'name', None)
    error_code = type(exception).__name__ if exception is not None else 'task_failure'
    log_event('core', 'job.fail', OUTCOME_FAILURE, error_code=error_code if error_code.replace('_', '').isalnum() else 'task_failure', job_name=job_name)
    logger.error('Celery task %s failed with %s', job_name or 'unknown', error_code)
