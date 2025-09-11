from collections import defaultdict

from django.conf import settings
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from favorites.models import Favorite
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from shopping_cart.models import ShoppingCart

from .filters import RecipeFilter
from .models import Ingredient, Recipe, RecipeIngredient, Tag
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    TagSerializer,
)
from .serializers_shot import RecipeShortSerializer


class RecipeShortLinkView(View):
    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return redirect(f"{frontend_url}/recipes/{recipe.pk}/",
                        permanent=True)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        is_fav = self.request.query_params.get('is_favorited') == '1'
        is_in_cart = self.request.query_params.get(
            'is_in_shopping_cart') == '1'

        if is_fav and self.request.user.is_authenticated:
            queryset = queryset.filter(
                favorited_by__user=self.request.user
            ).distinct()

        if is_in_cart and self.request.user.is_authenticated:
            queryset = queryset.filter(
                in_carts__user=self.request.user
            ).distinct()

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe)

        if not created:
            return Response(
                {'detail': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeShortSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        deleted, _ = Favorite.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def add_to_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not cart_item.exists():
            return Response(
                {'detail': 'Рецепт не найден в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        recipe_ingredients = RecipeIngredient.objects.filter(
            recipe__in_carts__user=user
        ).select_related('ingredient')
        ingredients = defaultdict(int)
        for ri in recipe_ingredients:
            key = (ri.ingredient.name, ri.ingredient.measurement_unit)
            ingredients[key] += ri.amount
        lines = [
            f"{name} ({unit}) — {amount}" for (name, unit), amount in
            ingredients.items()
        ]
        content = "\n".join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        path = reverse('recipe_short_link', args=[recipe.short_link])
        full_url = request.build_absolute_uri(path)
        return Response({"short-link": full_url}, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        qs = Ingredient.objects.all()
        q = (self.request.query_params.get('name')
             or self.request.query_params.get('search'))
        if q:
            q_normalized = q.strip()
            qs = qs.filter(name__icontains=q_normalized).annotate(
                priority=Case(
                    When(name__istartswith=q_normalized, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            ).order_by('priority', 'name')
        return qs
