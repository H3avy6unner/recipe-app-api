"""
Tests for recipe API.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Get detail url for recipe"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_user(**kwarg):
    """Helper function to create a samole user"""
    defaults = {
        "email": "test@example.com",
        "password": "TestPass1234",
        "name": "Test Name",
    }
    defaults.update(kwarg)
    return get_user_model().objects.create(**defaults)


def create_recipe(user, **kwargs):
    """Helper function to create a sample recipe"""
    defaults = {
        "title": "Sample Recipe title",
        "description": "Sample description for a Recipe",
        "time_minutes": 22,
        "price": Decimal("25.5"),
        "link": "http://www.example.com/recipe.pdf",
    }
    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeTests(TestCase):
    """Tests for unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        return super().setUp()

    def test_auth_is_required(self):
        """Test auth is required for call the API."""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeTests(TestCase):
    """Tests for authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        return super().setUp()

    def test_retrive_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_is_limited_to_user(self):
        """Test recipe list is limited to authenticated user"""
        other_user = create_user(
            email="test2@example.com",
            password="ZrddzÜsdd2345",
            name="Test2 Name",
        )
        create_recipe(user=self.user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test create recipe"""
        payload = {
            "title": "Test Title",
            "time_minutes": 30,
            "price": Decimal("5.99"),
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_partial_update(self):
        """Test Partial update a recipe"""
        recipe = create_recipe(user=self.user)
        original_price = recipe.price
        payload = {"title": "New Title"}
        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.price, original_price)

    def test_full_update(self):
        """Test full update for a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {
            "title": "New Title",
            "description": "New Sample description for a Recipe",
            "time_minutes": 40,
            "price": Decimal("30.99"),
            "link": "http://www.example.com/new-recipe.pdf",
        }
        url = detail_url(recipe_id=recipe.id)

        res = self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_recipe_user_error(self):
        """Test Update recipe user raises error"""

        recipe = create_recipe(user=self.user)
        new_user = create_user(
            email="test2@example.com",
            password="Test2Pass21234",
            name="Test2 Name",
        )
        url = detail_url(recipe_id=recipe.id)

        self.client.patch(url, {"user": new_user})
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_other_users_recipe_error(self):
        """Test get error if trying delete other users recipe"""
        new_user = create_user(
            email="test2@example.com",
            password="Test2Pass21234",
            name="Test2 Name",
        )
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal("2.50"),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        print(res.status_code, res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test create a recipe with existing tags"""
        tag_indian = Tag.objects.create(name="indian", user=self.user)
        payload = {
            "title": "Pongal",
            "time_minutes": 50,
            "price": Decimal("4.50"),
            "tags": [{"name": "indian"}, {"name": "Breakfast"}],
        }

        res = self.client.post(RECIPE_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating recipe"""
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag to an existing recipe"""
        recipe = create_recipe(user=self.user)
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe.tags.add(tag_breakfast)
        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")

        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test Clear alls tags from recipe"""
        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(user=self.user, name="Dessert")
        recipe.tags.add(tag)

        payload = {
            "tags": []
        }
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            "title": "Tacos",
            "time_minutes": 50,
            "price": Decimal("5.50"),
            "ingredients": [{"name": "Flower"}, {"name": "Salt"}],
        }

        res = self.client.post(RECIPE_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient["name"],
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test create a new recipe with existing ingredients"""
        ingrediant = Ingredient.objects.create(user=self.user, name="Lemon")
        payload = {
            "title": "Vietnamese Soup",
            "time_minutes": 30,
            "price": "6.50",
            "ingredients": [{"name": "Lemon"}, {"name": "Fish Sauce"}]
        }
        res = self.client.post(RECIPE_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingrediant, recipe.ingredients.all())
        for ingrediant in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingrediant["name"]
            ).exists()
            self.assertTrue(exists)
