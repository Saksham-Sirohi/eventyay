from unittest.mock import MagicMock
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
import pytest

from eventyay.multidomain.views import VideoAdminRedirectView, VideoSPAView


def test_video_admin_redirect_view():
    factory = RequestFactory()
    request = factory.get('/video/admin/rooms?tab=all')
    view = VideoAdminRedirectView.as_view()
    response = view(request, organizer='demo-org', event='demo-event', subpath='rooms')
    assert response.status_code == 302
    assert response['Location'] == '/video/event/demo-org/demo-event/rooms?tab=all'


def test_video_admin_redirect_view_root():
    factory = RequestFactory()
    request = factory.get('/video/admin/')
    view = VideoAdminRedirectView.as_view()
    response = view(request, organizer='demo-org', event='demo-event')
    assert response.status_code == 302
    assert response['Location'] == '/video/event/demo-org/demo-event/'


def test_video_spa_view_unauthenticated_organizer_redirects_to_login(monkeypatch):
    factory = RequestFactory()
    request = factory.get('/video/event/demo-org/demo-event/')
    request.user = MagicMock()
    request.user.is_authenticated = False

    fake_event = MagicMock()
    fake_event.slug = 'demo-event'
    fake_event.organizer.slug = 'demo-org'

    monkeypatch.setattr(
        'eventyay.multidomain.views.Event.objects.select_related',
        lambda *args: MagicMock(get=lambda **kwargs: fake_event),
    )

    view = VideoSPAView.as_view(is_organizer=True)
    response = view(request, organizer='demo-org', event='demo-event')
    assert response.status_code == 302
    assert '/login' in response['Location'] or 'login' in response['Location']


def test_video_spa_view_unauthorized_organizer_raises_permission_denied(monkeypatch):
    factory = RequestFactory()
    request = factory.get('/video/event/demo-org/demo-event/')
    request.user = MagicMock()
    request.user.is_authenticated = True
    request.user.is_staff = False
    request.user.is_superuser = False
    request.user.has_event_permission.return_value = False
    request.user.has_organizer_permission.return_value = False

    fake_event = MagicMock()
    fake_event.slug = 'demo-event'
    fake_event.organizer.slug = 'demo-org'

    monkeypatch.setattr(
        'eventyay.multidomain.views.Event.objects.select_related',
        lambda *args: MagicMock(get=lambda **kwargs: fake_event),
    )

    view = VideoSPAView.as_view(is_organizer=True)
    with pytest.raises(PermissionDenied):
        view(request, organizer='demo-org', event='demo-event')


def test_get_user_with_platform_user(monkeypatch):
    from eventyay.base.services.user import get_user

    fake_event = MagicMock()
    fake_event.id = 1
    fake_event.slug = 'demo-event'
    fake_event.organizer = MagicMock()
    fake_event.organizer.slug = 'demo-org'

    fake_platform_user = MagicMock()
    fake_platform_user.email = 'organizer@example.com'
    fake_platform_user.fullname = 'Demo Organizer'
    fake_platform_user.is_staff = True
    fake_platform_user.get_event_permission_set.return_value = {'can_change_event_settings'}

    fake_video_user = MagicMock()
    fake_video_user.id = 'user-123'
    fake_video_user.traits = ['admin']

    monkeypatch.setattr('eventyay.eventyay_common.video.traits_sync.apply_live_team_video_traits', lambda event, token_id, traits, **kwargs: traits)
    monkeypatch.setattr('eventyay.base.services.user.get_user_by_token_id', lambda event_id, token_id: fake_video_user)
    monkeypatch.setattr('eventyay.base.services.user.get_user_by_id', lambda event_id, user_id: fake_video_user)
    monkeypatch.setattr('eventyay.base.services.user.update_user', lambda event_id, id, **kwargs: fake_video_user)
    monkeypatch.setattr('eventyay.base.services.user.apply_video_jwt_contact_to_profile', lambda user, event_id, token_id: None)

    user = get_user(fake_event, with_platform_user=fake_platform_user)
    assert user == fake_video_user


def test_video_announcements_live_feature_default():
    from eventyay.base.services.event import _config_serializer

    fake_event = MagicMock()
    fake_event.id = 1
    fake_event.slug = 'demo-event'
    fake_event.config = {'live_features': {'chat_rooms': True}}
    fake_event.locale = 'en'
    fake_event.roles = {}
    fake_event.trait_grants = {}
    fake_event.timezone = 'UTC'

    data = _config_serializer(fake_event).data
    assert data['live_features']['announcements'] is True
    assert data['live_features']['chat_rooms'] is True


@pytest.mark.asyncio
async def test_announcement_module_disabled_check():
    from unittest.mock import AsyncMock
    from eventyay.features.live.modules.announcement import AnnouncementModule

    fake_consumer = MagicMock()
    fake_consumer.user = MagicMock()
    fake_consumer.event = MagicMock()
    fake_consumer.event.has_permission_async = AsyncMock(return_value=True)
    fake_consumer.event.config = {'live_features': {'announcements': False}}
    fake_consumer.send_error = AsyncMock()

    module = AnnouncementModule(fake_consumer)
    await module.create_announcement({'text': 'Hello'})
    fake_consumer.send_error.assert_called_once_with(code='announcements.disabled')


def test_video_permission_definitions_mapping():
    from eventyay.eventyay_common.video.permissions import (
        collect_user_video_traits,
        VIDEO_PERMISSION_DEFINITIONS,
    )

    slug = 'test-conf'
    # Test individual permissions
    traits = collect_user_video_traits(slug, ['can_video_manage_content'])
    assert traits == [f'eventyay-video-event-{slug}-video-content-manager']

    traits = collect_user_video_traits(slug, ['can_video_moderate'])
    assert traits == [f'eventyay-video-event-{slug}-video-moderator']

    traits = collect_user_video_traits(slug, ['can_video_manage_kiosks'])
    assert traits == [f'eventyay-video-event-{slug}-video-kiosk-manager']

    traits = collect_user_video_traits(slug, ['can_video_view_analytics'])
    assert traits == [f'eventyay-video-event-{slug}-video-analyst']

    traits = collect_user_video_traits(slug, ['can_change_config'])
    assert traits == [f'eventyay-video-event-{slug}-video-config-manager']

    traits = collect_user_video_traits(slug, ['can_change_event_settings'])
    assert traits == [f'eventyay-video-event-{slug}-video-config-manager']

    # Non-video permissions yield no video traits
    traits = collect_user_video_traits(slug, ['can_change_submissions', 'can_view_orders'])
    assert traits == []


def test_apply_live_team_video_traits_no_video_permissions(monkeypatch):
    from eventyay.eventyay_common.video.traits_sync import apply_live_team_video_traits

    fake_event = MagicMock()
    fake_event.slug = 'demo-event'
    fake_event.organizer = MagicMock()

    fake_platform_user = MagicMock()
    fake_platform_user.is_staff = True  # Staff user, but no active staff session!
    fake_platform_user.is_superuser = False
    fake_platform_user.has_active_staff_session.return_value = False
    fake_platform_user.get_event_permission_set.return_value = {'can_change_submissions'}

    monkeypatch.setattr(
        'eventyay.base.services.user.resolve_account_fields_by_token_ids',
        lambda ids: {'token123': {'email': 'user@example.com'}},
    )
    monkeypatch.setattr(
        'eventyay.base.services.user._ticket_lookup',
        lambda accounts, tid: {'email': 'user@example.com'},
    )
    monkeypatch.setattr(
        'eventyay.eventyay_common.video.traits_sync.User.objects.filter',
        lambda **kwargs: MagicMock(order_by=lambda *args: MagicMock(first=lambda: fake_platform_user)),
    )

    initial_traits = ['attendee', 'eventyay-video-event-demo-event', 'eventyay-video-event-demo-event-organizer', 'admin']
    result = apply_live_team_video_traits(fake_event, 'token123', initial_traits)

    # 'admin' must be removed, and no video managed traits added
    assert 'admin' not in result
    assert f'eventyay-video-event-demo-event-video-content-manager' not in result
    assert f'eventyay-video-event-demo-event-video-moderator' not in result
    assert f'eventyay-video-event-demo-event-video-kiosk-manager' not in result
    assert f'eventyay-video-event-demo-event-video-analyst' not in result
    assert f'eventyay-video-event-demo-event-video-config-manager' not in result
    assert result == ['attendee', 'eventyay-video-event-demo-event', 'eventyay-video-event-demo-event-organizer']


def test_apply_live_team_video_traits_with_active_staff_session(monkeypatch):
    from eventyay.eventyay_common.video.traits_sync import apply_live_team_video_traits

    fake_event = MagicMock()
    fake_event.slug = 'demo-event'
    fake_event.organizer = MagicMock()

    fake_platform_user = MagicMock()
    fake_platform_user.is_staff = True
    fake_platform_user.is_superuser = False
    fake_platform_user.has_active_staff_session.return_value = True
    fake_platform_user.get_event_permission_set.return_value = set()

    monkeypatch.setattr(
        'eventyay.base.services.user.resolve_account_fields_by_token_ids',
        lambda ids: {'token123': {'email': 'user@example.com'}},
    )
    monkeypatch.setattr(
        'eventyay.base.services.user._ticket_lookup',
        lambda accounts, tid: {'email': 'user@example.com'},
    )
    monkeypatch.setattr(
        'eventyay.eventyay_common.video.traits_sync.User.objects.filter',
        lambda **kwargs: MagicMock(order_by=lambda *args: MagicMock(first=lambda: fake_platform_user)),
    )

    initial_traits = ['attendee', 'eventyay-video-event-demo-event', 'eventyay-video-event-demo-event-organizer']
    result = apply_live_team_video_traits(fake_event, 'token123', initial_traits)

    assert 'admin' in result


def test_apply_live_team_video_traits_with_direct_platform_user():
    from eventyay.eventyay_common.video.traits_sync import apply_live_team_video_traits

    fake_event = MagicMock()
    fake_event.slug = 'demo-event'
    fake_event.organizer = MagicMock()

    fake_platform_user = MagicMock()
    fake_platform_user.is_staff = False
    fake_platform_user.is_superuser = False
    fake_platform_user.get_event_permission_set.return_value = {'can_video_manage_content', 'can_change_event_settings'}

    initial_traits = ['attendee', 'eventyay-video-event-demo-event', 'eventyay-video-event-demo-event-organizer']
    result = apply_live_team_video_traits(
        fake_event,
        'token123',
        initial_traits,
        platform_user=fake_platform_user,
    )

    assert 'eventyay-video-event-demo-event-video-content-manager' in result
    assert 'eventyay-video-event-demo-event-video-config-manager' in result

