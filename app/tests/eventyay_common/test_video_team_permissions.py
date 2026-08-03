import pytest

from eventyay.base.models import Team
from eventyay.core.permissions import Permission
from eventyay.eventyay_common.video.permissions import (
    VIDEO_PERMISSION_DEFINITIONS,
    collect_user_video_traits,
)


@pytest.mark.django_db
def test_collect_user_video_traits_uses_consolidated_fields(event):
    traits = collect_user_video_traits(
        event.slug,
        {
            'can_video_manage_content',
            'can_video_moderate',
            'can_video_view_analytics',
            'can_change_config',
        },
    )
    assert set(traits) == {
        f'eventyay-video-event-{event.slug}-video-content-manager',
        f'eventyay-video-event-{event.slug}-video-moderator',
        f'eventyay-video-event-{event.slug}-video-analyst',
        f'eventyay-video-event-{event.slug}-video-config-manager',
    }


@pytest.mark.django_db
def test_content_manager_trait_grants_exhibition_and_poster(event):
    trait = f'eventyay-video-event-{event.slug}-video-content-manager'
    assert event.has_permission_implicit(
        traits=[trait],
        permissions=[
            Permission.EVENT_ROOMS_CREATE_EXHIBITION,
            Permission.EVENT_ROOMS_CREATE_POSTER,
            Permission.ROOM_UPDATE,
        ],
    )


@pytest.mark.django_db
def test_moderator_trait_covers_former_dashboard_gaps(event):
    trait = f'eventyay-video-event-{event.slug}-video-moderator'
    assert event.has_permission_implicit(
        traits=[trait],
        permissions=[
            Permission.ROOM_ANNOUNCE,
            Permission.ROOM_VIEWERS,
            Permission.ROOM_BBB_RECORDINGS,
            Permission.EVENT_ANNOUNCE,
            Permission.EVENT_USERS_LIST,
        ],
    )


@pytest.mark.django_db
def test_analytics_does_not_imply_configuration(event):
    analyst = f'eventyay-video-event-{event.slug}-video-analyst'
    config = f'eventyay-video-event-{event.slug}-video-config-manager'
    assert event.has_permission_implicit(
        traits=[analyst],
        permissions=[Permission.EVENT_GRAPHS],
    )
    assert not event.has_permission_implicit(
        traits=[analyst],
        permissions=[Permission.EVENT_UPDATE],
    )
    assert event.has_permission_implicit(
        traits=[config],
        permissions=[Permission.EVENT_UPDATE],
    )
    assert not event.has_permission_implicit(
        traits=[config],
        permissions=[Permission.EVENT_GRAPHS],
    )


def test_video_permission_definitions_match_option_a():
    assert set(VIDEO_PERMISSION_DEFINITIONS) == {
        'can_video_manage_content',
        'can_video_moderate',
        'can_video_manage_kiosks',
        'can_video_view_analytics',
        'can_change_config',
    }


@pytest.mark.django_db
def test_team_model_exposes_only_consolidated_video_fields(organizer):
    team = Team.objects.create(
        organizer=organizer,
        name='Video ops',
        can_video_manage_content=True,
        can_video_moderate=True,
        can_change_config=True,
    )
    perms = team.permission_set()
    assert 'can_video_manage_content' in perms
    assert 'can_video_moderate' in perms
    assert 'can_change_config' in perms
    assert 'can_video_create_stages' not in perms
    assert 'can_video_manage_users' not in perms
    assert 'can_video_manage_configuration' not in perms
