from django.db import migrations
from django.db.models import QuerySet


def remove_default_speaker_questions(apps, schema_editor):
    """Remove seeded Job Title and Organization questions that have no responses.

    Answer and AnswerOption use on_delete=PROTECT. Questions that already have
    either are left in place so those responses are not deleted.
    """
    TalkQuestion = apps.get_model('base', 'TalkQuestion')
    Answer = apps.get_model('base', 'Answer')
    AnswerOption = apps.get_model('base', 'AnswerOption')

    questions = QuerySet(model=TalkQuestion).filter(
        import_key__in=['speaker_job_title', 'speaker_organization'],
    )
    answered_ids = QuerySet(model=Answer).filter(question__in=questions).values_list('question_id', flat=True)
    option_ids = QuerySet(model=AnswerOption).filter(question__in=questions).values_list('question_id', flat=True)
    questions.exclude(pk__in=answered_ids).exclude(pk__in=option_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0077_admin_message_center'),
    ]

    operations = [
        migrations.RunPython(remove_default_speaker_questions, reverse_code=migrations.RunPython.noop),
    ]
