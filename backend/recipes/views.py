from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Case, Count, IntegerField, Value, When
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .models import Favorite, Follow, Ingredient, Recipe, ShoppingCart, Tag
from .shopping_list import create_shopping_list_text
from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionAuthorSerializer,
    TagSerializer,
    UserReadSerializer,
)

User = get_user_model()


def recipe_short_link(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f"{settings.FRONTEND_URL}/recipes/{recipe.id}/")


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def add_recipe(self, request, model, recipe, message):
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {
                    'detail': message,
                    'recipe': {'id': recipe.id, 'name': recipe.name},
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=request.user, recipe=recipe)
        return Response(
            RecipeShortSerializer(
                recipe,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def remove_recipe(self, request, model, recipe):
        get_object_or_404(model, user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        is_fav = self.request.query_params.get('is_favorited') == '1'
        is_in_cart = self.request.query_params.get(
            'is_in_shopping_cart') == '1'

        if is_fav and self.request.user.is_authenticated:
            queryset = queryset.filter(
                favorites__user=self.request.user
            ).distinct()

        if is_in_cart and self.request.user.is_authenticated:
            queryset = queryset.filter(
                in_carts__user=self.request.user
            ).distinct()

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        return self.add_recipe(
            request,
            Favorite,
            self.get_object(),
            message='Рецепт уже в избранном'
        )

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self.remove_recipe(request, Favorite, self.get_object())

    @action(detail=True, methods=['post'], url_path='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def add_to_shopping_cart(self, request, pk=None):
        return self.add_recipe(
            request,
            ShoppingCart,
            self.get_object(),
            message='Рецепт уже в списке покупок'
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self.remove_recipe(request, ShoppingCart, self.get_object())

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        content = create_shopping_list_text(request.user)
        buf = BytesIO(content.encode('utf-8'))
        buf.seek(0)
        return FileResponse(
            buf,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain; charset=utf-8',
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound('Recipe not found')

        return Response(
            {'short-link': request.build_absolute_uri(
                reverse(
                    'recipe_short_link',
                    kwargs={'recipe_id': pk}))})


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


class UsersViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserReadSerializer
    permission_classes = [AllowAny]

    def _author_payload(self, u):
        return {
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
        }

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = (
            User.objects
            .filter(subscribers__user=request.user)
            .annotate(recipes_count=Count('recipes', distinct=True))
            .distinct()
        )
        page = self.paginate_queryset(authors)
        data = SubscriptionAuthorSerializer(
            page if page is not None else authors,
            many=True,
            context={'request': request},
        ).data
        return (
            self.get_paginated_response(data)
            if page is not None
            else Response({'count': len(data), 'next': None, 'previous': None,
                           'results': data})
        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'DELETE':
            deleted, _ = Follow.objects.filter(
                user_id=user.id, following_id=author.id
            ).delete()
            if not deleted:
                raise ValidationError({
                    'errors': 'Вы не были подписаны на этого автора.',
                    'author': self._author_payload(author),
                })
            return Response(status=status.HTTP_204_NO_CONTENT)

        if user.id == author.id:
            raise ValidationError({
                'errors': 'Нельзя подписаться на самого себя.',
                'author': self._author_payload(author),
            })

        _, created = Follow.objects.get_or_create(
            user_id=user.id, following_id=author.id
        )
        if not created:
            raise ValidationError({
                'errors': 'Вы уже подписаны на этого автора.',
                'author': self._author_payload(author),
            })

        author = (
            User.objects.filter(pk=author.pk)
            .annotate(recipes_count=Count('recipes', distinct=True))
            .get()
        )
        data = SubscriptionAuthorSerializer(author,
                                            context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.avatar = ''
        user.save()
        return Response(
            {'status': 'avatar reset'},
            status=status.HTTP_200_OK,
        )

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='recipes'
    )
    def user_recipes(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        recipes = author.recipes.all()
        serializer = RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        """Профиль текущего пользователя с аватаром."""

        return Response(UserReadSerializer(
            request.user,
            context={'request': request}
        ).data,
            status=status.HTTP_200_OK)
