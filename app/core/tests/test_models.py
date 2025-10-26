"""
Tests for models.
"""
from unittest.mock import patch

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def create_user(email="test@example.com", password="TestPass1234"):
    """Helper function for creating a user"""
    return get_user_model().objects.create(email=email, password=password)


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

    def test_create_recipe(self):
        """Test Create new recipe"""
        user = get_user_model().objects.create(
            email="test@example.com",
            password="Testtest88",
            name="Test Name",
        )

        recipe = models.Recipe(
            user=user,
            title="Simple Recipe Name",
            time_minutes=5,
            price=Decimal(5.50),
            description="Hier steht Werbung",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test Create a tag is successfull"""
        user = create_user()
        tag = models.Tag.objects.create(
            user=user,
            name="TestTag1",
        )

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test create an ingredient"""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name="Ingredient1",
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test Generation Image Path"""
        uuid = "Test-UUID"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
