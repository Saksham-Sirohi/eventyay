import pytest
from django_scopes import scope

from eventyay.base.models import Answer, TalkQuestion, TalkQuestionTarget, TalkQuestionVariant
from eventyay.common.session_video import (
    SESSION_VIDEO_IMPORT_KEY,
    get_session_video_question,
    get_submission_video_url,
    set_submission_video_url,
)


@pytest.mark.django_db
def test_get_session_video_question_creates_canonical_field(event):
    with scope(event=event):
        assert get_session_video_question(event, create=False) is None
        question = get_session_video_question(event, create=True)
        assert question is not None
        assert question.variant == TalkQuestionVariant.VIDEO
        assert question.target == TalkQuestionTarget.SUBMISSION
        assert question.import_key == SESSION_VIDEO_IMPORT_KEY
        assert question.is_public is True
        assert get_session_video_question(event, create=True).pk == question.pk
        assert TalkQuestion.all_objects.filter(
            event=event,
            target=TalkQuestionTarget.SUBMISSION,
            variant=TalkQuestionVariant.VIDEO,
        ).count() == 1


@pytest.mark.django_db
def test_get_session_video_question_adopts_existing_video_field(event):
    with scope(event=event):
        existing = TalkQuestion.objects.create(
            event=event,
            question='Recording',
            variant=TalkQuestionVariant.VIDEO,
            target=TalkQuestionTarget.SUBMISSION,
            is_public=False,
        )
        question = get_session_video_question(event, create=True)
        assert question.pk == existing.pk
        question.refresh_from_db()
        assert question.import_key == SESSION_VIDEO_IMPORT_KEY
        assert question.is_public is True


@pytest.mark.django_db
def test_set_submission_video_url_creates_updates_and_clears(event, submission):
    url = 'https://youtu.be/dQw4w9WgXcQ?t=90'
    with scope(event=event):
        assert get_submission_video_url(submission) == ''
        stored = set_submission_video_url(submission, url)
        assert stored == url
        question = get_session_video_question(event, create=False)
        assert question is not None
        assert get_submission_video_url(submission) == url
        assert Answer.objects.filter(question=question, submission=submission).count() == 1

        updated = 'https://vimeo.com/123456789#t=1m30s'
        assert set_submission_video_url(submission, updated) == updated
        assert get_submission_video_url(submission) == updated
        assert Answer.objects.filter(question=question, submission=submission).count() == 1

        assert set_submission_video_url(submission, '') == ''
        assert get_submission_video_url(submission) == ''
        assert not Answer.objects.filter(question=question, submission=submission).exists()


@pytest.mark.django_db
def test_set_submission_video_url_rejects_invalid(event, submission):
    with scope(event=event):
        with pytest.raises(ValueError):
            set_submission_video_url(submission, 'https://example.com/watch')
        assert get_session_video_question(event, create=False) is None
        assert get_submission_video_url(submission) == ''
