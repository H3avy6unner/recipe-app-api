"""
Tests for ingredients API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Helper function to return detail-url"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="user@example.com", password="TestPass1234"):
    """Helper function to return a User"""
    return get_user_model().objects.create(email=email, password=password)


def create_ingredient(user, name="Test"):
    """Helper function to return an ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientsTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        return super().setUp()

    def test_auth_required(self):
        """Test authentication is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        return super().setUp()

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        create_ingredient(user=self.user, name="Kale")
        create_ingredient(user=self.user, name="Vanilla")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user"""
        user2 = create_user(email="user2@example.com", password="TestPass123456")
        ingredient = create_ingredient(self.user, name="Salt")
        create_ingredient(user2, name="Pepper")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_upgrade_ingrediant(self):
        """Test upgrading ingredient"""
        ingredient = create_ingredient(user=self.user, name="Cilantro")

        payload = {
            "name": "Cinnamon"
        }
        url = detail_url(ingredient_id=ingredient.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_deleting_ingrediant(self):
        """Test deleting an ingredient"""
        ingredient = create_ingredient(user=self.user, name="Lettuce")

        url = detail_url(ingredient_id=ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigne_to_recipes(self):
        """Test listing ingredients by those assigned to recipes"""
        in1 = Ingredient.objects.create(user=self.user, name="Sample Ingredient 1")
        in2 = Ingredient.objects.create(user=self.user, name="Sample Ingredient 2")
        recipe = Recipe.objects.create(
            user=self.user,
            title="Sample Recipe ",
            time_minutes=5,
            price=Decimal("2.50"),
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredient_unique(self):
        """Test filtered ingredients returns a unique list."""
        ing = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")
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
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
