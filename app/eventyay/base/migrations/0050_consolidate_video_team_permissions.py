from django.db import migrations, models


LEGACY_CONTENT_FIELDS = (
    'can_video_create_stages',
    'can_video_create_channels',
    'can_video_manage_rooms',
)

LEGACY_MODERATE_FIELDS = (
    'can_video_manage_announcements',
    'can_video_view_users',
    'can_video_manage_users',
    'can_video_manage_polls_questions',
)

REMOVED_FIELDS = (
    'can_video_create_stages',
    'can_video_create_channels',
    'can_video_direct_message',
    'can_video_manage_announcements',
    'can_video_view_users',
    'can_video_manage_users',
    'can_video_manage_rooms',
    'can_video_manage_polls_questions',
)

CONSOLIDATED_VIDEO_ROLES = {
    'video_content_manager': [
        'event:rooms.create.stage',
        'event:rooms.create.chat',
        'event:rooms.create.bbb',
        'event:rooms.create.exhibition',
        'event:rooms.create.poster',
        'room:update',
        'room:delete',
    ],
    'video_moderator': [
        'event:announce',
        'room:announce',
        'event:users.list',
        'event:users.manage',
        'room:chat.moderate',
        'room:viewers',
        'room:bbb.recordings',
        'room:question.read',
        'room:question.moderate',
        'room:poll.read',
        'room:poll.manage',
        'room:poll.early_results',
    ],
    'video_kiosk_manager': [
        'event:kiosks.manage',
    ],
    'video_analyst': [
        'event:graphs',
    ],
    'video_config_manager': [
        'event.update',
    ],
}

LEGACY_VIDEO_ROLES = (
    'video_stage_manager',
    'video_channel_manager',
    'video_announcement_manager',
    'video_user_viewer',
    'video_user_moderator',
    'video_room_manager',
    'video_poll_question_manager',
)


def migrate_video_permissions_forward(apps, schema_editor):
    Team = apps.get_model('base', 'Team')
    update_fields = [
        'can_video_manage_content',
        'can_video_moderate',
        'can_video_view_analytics',
        'can_change_config',
    ]
    for team in Team.objects.all().iterator():
        team.can_video_manage_content = any(
            getattr(team, field) for field in LEGACY_CONTENT_FIELDS
        )
        team.can_video_moderate = any(
            getattr(team, field) for field in LEGACY_MODERATE_FIELDS
        )
        had_video_config = bool(team.can_video_manage_configuration)
        # Old configuration toggle also granted analytics (event:graphs).
        team.can_video_view_analytics = had_video_config
        # In-video Event Config moves to the shared can_change_config permission.
        team.can_change_config = had_video_config
        team.save(update_fields=update_fields)

    Event = apps.get_model('base', 'Event')
    # Keep stored admin roles complete for staff/admin trait users.
    ADMIN_EXTRA_PERMISSIONS = (
        'event:kiosks.manage',
        'room:invite',
    )
    for event in Event.objects.exclude(roles=None).iterator():
        roles = dict(event.roles or {})
        changed = False
        for role_name, permissions in CONSOLIDATED_VIDEO_ROLES.items():
            if roles.get(role_name) != permissions:
                roles[role_name] = list(permissions)
                changed = True
        for legacy_role in LEGACY_VIDEO_ROLES:
            if legacy_role in roles:
                del roles[legacy_role]
                changed = True
        admin_perms = list(roles.get('admin') or [])
        if admin_perms:
            for perm in ADMIN_EXTRA_PERMISSIONS:
                if perm not in admin_perms:
                    admin_perms.append(perm)
                    changed = True
            roles['admin'] = admin_perms
        if changed:
            event.roles = roles
            event.save(update_fields=['roles'])


def migrate_video_permissions_backward(apps, schema_editor):
    Team = apps.get_model('base', 'Team')
    update_fields = list(REMOVED_FIELDS) + ['can_video_manage_configuration']
    for team in Team.objects.all().iterator():
        content = team.can_video_manage_content
        moderate = team.can_video_moderate
        team.can_video_create_stages = content
        team.can_video_create_channels = content
        team.can_video_manage_rooms = content
        team.can_video_manage_announcements = moderate
        team.can_video_view_users = moderate
        team.can_video_manage_users = moderate
        team.can_video_manage_polls_questions = moderate
        team.can_video_direct_message = False
        team.can_video_manage_configuration = bool(
            team.can_change_config or team.can_video_view_analytics
        )
        team.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0049_alter_talkquestion_variant_add_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='can_video_manage_content',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Create and edit stages, chat/video channels, exhibition booths, and poster '
                    'sessions; edit and delete rooms.'
                ),
                verbose_name='Video: Can manage rooms and content',
            ),
        ),
        migrations.AddField(
            model_name='team',
            name='can_video_moderate',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Announce globally and in rooms; list and moderate users; moderate chat; '
                    'see room viewers; manage polls and Q&A; access BBB recordings.'
                ),
                verbose_name='Video: Can moderate users and engagement',
            ),
        ),
        migrations.AddField(
            model_name='team',
            name='can_video_view_analytics',
            field=models.BooleanField(
                default=False,
                help_text='Allows viewing Eventyay Video statistics and analytics dashboards.',
                verbose_name='Video: Can view analytics',
            ),
        ),
        migrations.AddField(
            model_name='team',
            name='can_change_config',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Edit in-video Event Config such as theme, connection limits, and BBB defaults.'
                ),
                verbose_name='Can change config',
            ),
        ),
        migrations.RunPython(
            migrate_video_permissions_forward,
            migrate_video_permissions_backward,
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_create_stages',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_create_channels',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_direct_message',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_manage_announcements',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_view_users',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_manage_users',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_manage_rooms',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_manage_polls_questions',
        ),
        migrations.RemoveField(
            model_name='team',
            name='can_video_manage_configuration',
        ),
        migrations.AlterField(
            model_name='team',
            name='can_video_manage_kiosks',
            field=models.BooleanField(
                default=False,
                help_text='Allows creating and editing kiosk displays inside Eventyay Video.',
                verbose_name='Video: Can manage kiosks',
            ),
        ),
    ]
