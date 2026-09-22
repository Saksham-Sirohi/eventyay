import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed

from eventyay.base.models.auth_token import UserApiToken, generate_api_token
from eventyay.base.models.organizer import TeamAPIToken
from eventyay.common.auth import UserOrTeamTokenAuthentication


@pytest.mark.django_db
def test_user_or_team_token_accepts_user_api_token(orga_user, event):
    token_value = generate_api_token()
    token = UserApiToken.objects.create(
        name='user-token',
        user=orga_user,
        token=token_value,
    )
    token.events.set([event])

    user, auth = UserOrTeamTokenAuthentication().authenticate_credentials(token_value)
    assert user == orga_user
    assert auth == token


@pytest.mark.django_db
def test_user_or_team_token_accepts_team_api_token(orga_user, event):
    team = event.organizer.teams.filter(members=orga_user).first()
    assert team is not None
    token_value = generate_api_token()
    token = TeamAPIToken.objects.create(
        name='team-token',
        team=team,
        token=token_value,
    )

    user, auth = UserOrTeamTokenAuthentication().authenticate_credentials(token_value)
    assert isinstance(user, AnonymousUser)
    assert auth == token


@pytest.mark.django_db
def test_user_or_team_token_rejects_unknown_token():
    with pytest.raises(AuthenticationFailed):
        UserOrTeamTokenAuthentication().authenticate_credentials('not-a-real-token')
