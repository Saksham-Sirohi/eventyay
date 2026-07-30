import pytest
from django_scopes import scope

from eventyay.base.models import Answer, TalkQuestion, TalkQuestionTarget, TalkQuestionVariant
from eventyay.common.session_video import (
    SESSION_VIDEO_IMPORT_KEY,
    ensure_session_video_question,
    get_session_video_question,
    get_submission_video_url,
    get_submission_video_urls,
    set_submission_video_url,
    set_submission_video_urls,
)
from eventyay.common.video_embed import parse_video_urls
from eventyay.orga.forms.cfp import TalkQuestionForm
from eventyay.submission.forms import TalkQuestionsForm


@pytest.mark.django_db
def test_get_session_video_question_creates_canonical_field(event):
    with scope(event=event):
        assert get_session_video_question(event, create=False) is None
        question = get_session_video_question(event, create=True)
        assert question is not None
        assert question.variant == TalkQuestionVariant.VIDEO
        assert question.target == TalkQuestionTarget.SUBMISSION
        assert question.import_key == SESSION_VIDEO_IMPORT_KEY
        assert question.is_public is False
        assert question.active is True
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
        assert question.is_public is False


@pytest.mark.django_db
def test_ensure_session_video_question_deactivates_extra_fields(event):
    with scope(event=event):
        first = TalkQuestion.objects.create(
            event=event,
            question='Video A',
            variant=TalkQuestionVariant.VIDEO,
            target=TalkQuestionTarget.SUBMISSION,
            active=True,
        )
        second = TalkQuestion.objects.create(
            event=event,
            question='Video B',
            variant=TalkQuestionVariant.VIDEO,
            target=TalkQuestionTarget.SUBMISSION,
            active=True,
        )
        question = ensure_session_video_question(event)
        assert question.pk == first.pk
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.active is True
        assert first.import_key == SESSION_VIDEO_IMPORT_KEY
        assert second.active is False


@pytest.mark.django_db
def test_set_submission_video_url_creates_updates_and_clears(event, submission):
    url = 'https://youtu.be/dQw4w9WgXcQ?t=90'
    with scope(event=event):
        assert get_submission_video_url(submission) == ''
        stored = set_submission_video_url(submission, url)
        assert stored == url
        question = get_session_video_question(event, create=False)
        assert question is not None
        assert question.is_public is False
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
def test_set_submission_video_urls_stores_multiple(event, submission):
    urls = [
        'https://youtu.be/dQw4w9WgXcQ?t=90',
        'https://vimeo.com/123456789#t=1m30s',
    ]
    with scope(event=event):
        stored = set_submission_video_urls(submission, urls)
        assert stored == urls
        assert get_submission_video_urls(submission) == urls
        assert get_submission_video_url(submission) == '\n'.join(urls)
        question = get_session_video_question(event, create=False)
        assert Answer.objects.filter(question=question, submission=submission).count() == 1

        assert set_submission_video_urls(submission, []) == []
        assert get_submission_video_urls(submission) == []


@pytest.mark.django_db
def test_set_submission_video_url_rejects_invalid(event, submission):
    with scope(event=event):
        with pytest.raises(ValueError):
            set_submission_video_url(submission, 'https://example.com/watch')
        assert get_session_video_question(event, create=False) is None
        assert get_submission_video_url(submission) == ''


def test_parse_video_urls_splits_lines_and_dedupes():
    assert parse_video_urls('') == []
    assert parse_video_urls('https://youtu.be/aaa\nhttps://vimeo.com/1') == [
        'https://youtu.be/aaa',
        'https://vimeo.com/1',
    ]
    assert parse_video_urls('https://youtu.be/aaa\n\nhttps://youtu.be/aaa') == [
        'https://youtu.be/aaa',
    ]


@pytest.mark.django_db
def test_talk_question_form_hides_video_variant_on_create(event):
    with scope(event=event):
        form = TalkQuestionForm(event=event, initial={'target': TalkQuestionTarget.SUBMISSION})
        assert TalkQuestionVariant.VIDEO not in dict(form.fields['variant'].choices)


@pytest.mark.django_db
def test_session_video_hidden_from_speaker_questions_form(event, submission):
    with scope(event=event):
        question = ensure_session_video_question(event)
        speaker_form = TalkQuestionsForm(
            event=event,
            submission=submission,
            target=TalkQuestionTarget.SUBMISSION,
            include_session_video=False,
        )
        orga_form = TalkQuestionsForm(
            event=event,
            submission=submission,
            target=TalkQuestionTarget.SUBMISSION,
            include_session_video=True,
        )
        assert f'question_{question.pk}' not in speaker_form.fields
        assert f'question_{question.pk}' in orga_form.fields
