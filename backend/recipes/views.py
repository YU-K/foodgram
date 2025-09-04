from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from .filters import RecipeFilter
from .models import Recipe, Tag, Ingredient
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    RecipeCreateSerializer,
    RecipeSerializer,
    IngredientSerializer,
    TagSerializer,
)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


