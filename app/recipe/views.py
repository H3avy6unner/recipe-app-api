"""
Views for recipe APIs
"""
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeImageSerializer,
)
from core.models import Recipe, Tag, Ingredient


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma separeted list of IDs to filter"
            ),
            OpenApiParameter(
                "ingredients",
                OpenApiTypes.STR,
                description="Comma separated list of ingredient IDs to filter"
            )
        ]
    )
)
class RecipeViewset(viewsets.ModelViewSet):
    """View for listing der Recipie"""
    queryset = Recipe.objects.all()
    serializer_class = RecipeDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)

        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create new Recipe"""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT, enum=[0, 1],
                description="Filter by items assigned to recipes.",
            )
        ]
    )
)
class BaseRecipeAttrViewset(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin):
    """Base class for Recipe Attributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user"""
        assigned_only = bool(
            int(self.request.query_params.get("assigned_only", 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).order_by("-name").distinct()


class TagViewset(BaseRecipeAttrViewset):
    """Manage Tags in Database"""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientsViewset(BaseRecipeAttrViewset):
    """Manage Ingredients in Database"""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
