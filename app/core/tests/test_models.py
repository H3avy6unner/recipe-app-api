"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test Models."""

    def test_create_user_with_email_success(self):
        """Test user creating with an email is successsfull"""
        email = "test@example.com"
        password = "Testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test if Email for new created users is normalized"""
        sample_emails = [
            ["test1@EXAMPLE.COM", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.com", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_user_without_email_raise_error(self):
        """Test for user creation without email raises ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "Sample123")

    def test_create_superuser(self):
        """Test for superuser creation."""
        user = get_user_model().objects.create_superuser(
            email="test@example.com",
            password="Test123"
        )

        self.assertEqual(user.is_superuser, True)
        self.assertEqual(user.is_staff, True)
