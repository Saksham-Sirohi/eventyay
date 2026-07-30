"""Canonical per-session video link field helpers for organisers and public embeds."""

from __future__ import annotations

from django.db.models import Prefetch
from django.utils.translation import gettext, gettext_lazy as _
from django_scopes import scope
from i18nfield.strings import LazyI18nString

from eventyay.base.models import (
    Answer,
    TalkQuestion,
    TalkQuestionRequired,
    TalkQuestionTarget,
    TalkQuestionVariant,
)
from eventyay.common.video_embed import get_video_embed_info, parse_video_urls

SESSION_VIDEO_IMPORT_KEY = 'session_video'


def get_session_video_question(event, *, create: bool = False):
    """Return the event's single submission Video link field, optionally creating it.

    Prefers the field tagged with ``SESSION_VIDEO_IMPORT_KEY``. Otherwise adopts the
    first existing submission ``video`` question. When ``create`` is True and none
    exists, creates a public optional Video link field.
    """
    with scope(event=event):
        questions = TalkQuestion.all_objects.filter(
            event=event,
            target=TalkQuestionTarget.SUBMISSION,
            variant=TalkQuestionVariant.VIDEO,
        ).order_by('position', 'pk')

        tagged = questions.filter(import_key=SESSION_VIDEO_IMPORT_KEY).first()
        if tagged:
            return tagged

        existing = questions.first()
        if existing:
            update_fields = []
            if not existing.import_key:
                existing.import_key = SESSION_VIDEO_IMPORT_KEY
                update_fields.append('import_key')
            if create:
                if not existing.is_public:
                    existing.is_public = True
                    update_fields.append('is_public')
                if not existing.active:
                    existing.active = True
                    update_fields.append('active')
            if update_fields:
                existing.save(update_fields=update_fields)
            return existing

        if not create:
            return None

        return TalkQuestion.all_objects.create(
            event=event,
            variant=TalkQuestionVariant.VIDEO,
            target=TalkQuestionTarget.SUBMISSION,
            question=LazyI18nString.from_gettext(_('Video')),
            help_text=LazyI18nString.from_gettext(
                _(
                    'YouTube or Vimeo URLs (one per line) shown as embeds on the '
                    'public session page.'
                )
            ),
            question_required=TalkQuestionRequired.OPTIONAL,
            is_public=True,
            active=True,
            contains_personal_data=False,
            is_visible_to_reviewers=True,
            import_key=SESSION_VIDEO_IMPORT_KEY,
            is_imported=False,
        )


def get_submission_video_answer(submission):
    question = get_session_video_question(submission.event, create=False)
    if not question:
        return None
    with scope(event=submission.event):
        return (
            Answer.objects.filter(question=question, submission=submission)
            .select_related('question')
            .first()
        )


def get_submission_video_urls(submission) -> list[str]:
    answer = get_submission_video_answer(submission)
    return parse_video_urls(answer.answer if answer else '')


def get_submission_video_url(submission) -> str:
    """Return stored video URLs as a newline-joined string (empty when none)."""
    return '\n'.join(get_submission_video_urls(submission))


def set_submission_video_urls(submission, urls: list[str] | None) -> list[str]:
    """Create/update/clear session video answers.

    Empty ``urls`` clears the answer. Each non-empty value must be an embeddable
    YouTube/Vimeo URL. Returns the stored URL list (empty when cleared).
    """
    cleaned: list[str] = []
    seen: set[str] = set()
    for url in urls or []:
        raw = (url or '').strip()
        if not raw or raw in seen:
            continue
        if get_video_embed_info(raw) is None:
            raise ValueError(gettext('Please enter a valid YouTube or Vimeo URL.'))
        seen.add(raw)
        cleaned.append(raw)

    stored = '\n'.join(cleaned)
    question = get_session_video_question(submission.event, create=bool(cleaned))
    if not question:
        return []

    with scope(event=submission.event):
        answer = Answer.objects.filter(question=question, submission=submission).first()
        if not cleaned:
            if answer:
                answer.delete()
            return []

        if answer:
            answer.answer = stored
            answer.save(update_fields=['answer'])
        else:
            Answer.objects.create(question=question, submission=submission, answer=stored)
        return cleaned


def set_submission_video_url(submission, url: str | None) -> str:
    """Create/update/clear the session video answer from a single string.

    Multiple URLs may be separated by newlines. Empty ``url`` clears the answer.
    Returns the stored value as a newline-joined string (empty when cleared).
    """
    raw = (url or '').strip()
    if not raw:
        return '\n'.join(set_submission_video_urls(submission, []))
    return '\n'.join(set_submission_video_urls(submission, parse_video_urls(raw)))


def prefetch_submission_video_urls(queryset, event):
    """Prefetch canonical video answers onto a submission queryset for list views."""
    question = get_session_video_question(event, create=False)
    if not question:
        return queryset
    with scope(event=event):
        return queryset.prefetch_related(
            Prefetch(
                'answers',
                queryset=Answer.objects.filter(question=question).select_related('question'),
                to_attr='_session_video_answers',
            )
        )


def video_urls_from_prefetched_submission(submission) -> list[str]:
    answers = getattr(submission, '_session_video_answers', None)
    if answers is None:
        return get_submission_video_urls(submission)
    if not answers:
        return []
    return parse_video_urls(answers[0].answer or '')


def video_url_from_prefetched_submission(submission) -> str:
    return '\n'.join(video_urls_from_prefetched_submission(submission))
