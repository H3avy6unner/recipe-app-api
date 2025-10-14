"""Views for the user API."""

from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.authtoken.views import ObtainAuthToken
from user.serializer import UserModelSerializer, AuthTokenSerializer
from rest_framework.settings import api_settings
from rest_framework import authentication, permissions


class UserCreateAPIView(CreateAPIView):
    """Create User View"""
    serializer_class = UserModelSerializer


class CreateAuthToken(ObtainAuthToken):
    """Create new auth token for user."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserModelSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user"""
        return self.request.user
