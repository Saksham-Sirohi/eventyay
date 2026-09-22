from django.contrib.auth.models import AnonymousUser
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from eventyay.base.models.auth_token import UserApiToken
from eventyay.base.models.organizer import TeamAPIToken


class UserTokenAuthentication(TokenAuthentication):
    """Authenticate organiser API tokens created at ``/orga/me`` (``UserApiToken``)."""

    model = UserApiToken

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = (
                model.objects.active()
                .select_related('user')
                .prefetch_related('events')
                .get(token=key)
            )
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token.')

        if not token.is_active:
            raise exceptions.AuthenticationFailed('Token inactive or deleted.')

        return token.user, token


class UserOrTeamTokenAuthentication(TokenAuthentication):
    """Accept either ``UserApiToken`` (orga/me) or ``TeamAPIToken`` under ``Authorization: Token``.

    Both token types share the ``Token`` keyword. DRF stops at the first authenticator that
    raises ``AuthenticationFailed``, so a single class must try both models.
    """

    keyword = 'Token'

    def authenticate_credentials(self, key):
        try:
            token = (
                UserApiToken.objects.active()
                .select_related('user')
                .prefetch_related('events')
                .get(token=key)
            )
        except UserApiToken.DoesNotExist:
            token = None
        if token is not None:
            if not token.is_active:
                raise exceptions.AuthenticationFailed('Token inactive or deleted.')
            return token.user, token

        try:
            token = TeamAPIToken.objects.select_related('team', 'team__organizer').get(token=key)
        except TeamAPIToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token.')

        if not token.active:
            raise exceptions.AuthenticationFailed('Token inactive or deleted.')

        return AnonymousUser(), token
