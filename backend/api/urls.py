from django.urls import include, path
from recipes.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UsersViewSet,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet, basename='tags')
router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
