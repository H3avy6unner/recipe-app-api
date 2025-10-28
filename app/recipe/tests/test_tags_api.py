"""
Tests for Tags API.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import TagSerializer
from core.models import Tag, Recipe

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Helper function to get the detail url for tag"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="test@example.com", password="TestPass1234"):
    """Create Sample user"""
    return get_user_model().objects.create(email=email, password=password)


def create_tag(user, name="TestTag"):
    """Helper function to create tags"""
    return Tag.objects.create(user=user, name=name)


class PublicTagsApiTests(TestCase):
    """Tests unauthorized API requests"""

    def setUp(self):
        """Setting up for all tests in class"""
        self.client = APIClient()
        return super().setUp()

    def test_auth_required(self):
        """Test auth is required for retrieving Tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Tests authenticated API requests"""

    def setUp(self):
        """Setting up for all tests in class"""
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""
        create_tag(user=self.user, name="Vegan")
        create_tag(user=self.user, name="Desert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test Tags list is limited to authenticated user"""
        user2 = create_user(email="test2@example.com", password="Test2Pass212342")
        create_tag(user=user2, name="Fruity")
        tag = create_tag(user=self.user, name="Comfort Fruit")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating an existig Tag"""
        tag = create_tag(user=self.user, name="After Dinner")
        payload = {
            "name": "Dessert"
        }
        url = detail_url(tag_id=tag.id)

        res = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting an existing tag"""
        tag = create_tag(user=self.user, name="Breakfast")
        url = detail_url(tag_id=tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigne_to_recipes(self):
        """Test listing tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name="Sample Tag 1")
        tag2 = Tag.objects.create(user=self.user, name="Sample Tag 2")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Sample Recipe ",
            time_minutes=5,
            price=Decimal("2.50"),
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tag_unique(self):
        """Test filtered tags returns a unique list."""
        tag = Tag.objects.create(user=self.user, name="Eggs")
        Tag.objects.create(user=self.user, name="Lentils")
        recipe1 = Recipe.objects.create(
            title="Herb Eggs",
            time_minutes=20,
            price=Decimal("6.88"),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="Eggs Benedict",
            time_minutes=60,
            price=Decimal("4.90"),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
