"""
Test for user api.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    """Create and return new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the public features of the API"""

    def setUp(self):  # setUp-Function gilt für alle tests der Klasse und wird im Vorfeld ausgeführt
        self.client = APIClient()
        return super().setUp()

    def test_create_user_success(self):
        """Test a user creating is successfull"""
        payload = {
            "email": "test@example.com",
            "password": "testPass123",
            "name": "Test Name",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn(payload["password"], res.data)

    def test_user_with_email_exist_error(self):
        """Test return error if user already exist."""
        payload = {
            "email": "test@example.com",
            "password": "testPass123",
            "name": "Test Name",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password is less than 5 chars."""
        payload = {
            "email": "test@example.com",
            "password": "tP23",
            "name": "Test Name",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exist)

    def test_create_token_for_user(self):
        """Test for creating a token for valid user credentials."""
        user_details = {
            "name": "Test Name",
            "email": "test@example.com",
            "password": "test-User-Password1234"
        }
        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials are invalid"""
        user_details = {
            "name": "Test Name",
            "email": "test@example.com",
            "password": "test-User-Password1234"
        }
        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": "wrongPassword1234",
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test returns error if password is blank"""
        payload = {
            "email": "test@example.com",
            "password": "",
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):  # Gilt für alle test/def der Klasse. Wird im Vorfeld ausgeführt.
        self.user = create_user(
            email="test@example.com",
            password="TestPass1234",
            name="Test Name",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)  # Nimmt eine erfolgte Authentisierung an (nicht jeder Test belastet die API)
        return super().setUp()

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            "email": self.user.email,
            "name": self.user.name,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user."""

        payload = {
            "name": "New Name",
            "password": "NewPass1234",
        }

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
