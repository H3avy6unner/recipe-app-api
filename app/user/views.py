"""Views for the user API."""

from rest_framework.generics import CreateAPIView
from user.serializer import UserModelSerializer


class UserCreateAPIView(CreateAPIView):
    """Create User View"""
    serializer_class = UserModelSerializer
