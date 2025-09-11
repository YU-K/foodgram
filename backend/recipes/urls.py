from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeShortLinkView,
    RecipeViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

urlpatterns = [
    path('s/<slug:short_link>/', RecipeShortLinkView.as_view(),
         name='recipe_short_link'),
    path('', include(router.urls)),
]
