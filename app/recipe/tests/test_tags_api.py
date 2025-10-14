"""
Tests for Tags API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import TagSerializer
from core.models import Tag

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
