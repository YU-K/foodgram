from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionAuthorSerializer,
    TagSerializer,
    UserReadSerializer,
)
from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from recipes.shopping_list import create_shopping_list_text

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def add_recipe(self, request, model, recipe):
        obj, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            raise ValidationError({
                'detail':
                    f'Рецепт {recipe.name} уже '
                    f'добавлен «{model._meta.verbose_name_plural}».'
            })
        return Response(
            RecipeShortSerializer(
                recipe,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def remove_recipe(self, request, model, recipe_id):
        get_object_or_404(
            model, user=request.user, recipe_id=recipe_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        )

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self.remove_recipe(request, Favorite, pk)

    @action(detail=True, methods=['post'], url_path='shopping_cart',
            permission_classes=(IsAuthenticated,))
    def add_to_shopping_cart(self, request, pk=None):
        return self.add_recipe(
            request,
            ShoppingCart,
            self.get_object(),
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self.remove_recipe(request, ShoppingCart, self.get_object())

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        return FileResponse(
            create_shopping_list_text(request.user),
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain',
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError({'detail': f'Рецепт с id={pk} не найден.'})

        return Response(
            {'short-link': request.build_absolute_uri(
                reverse(
                    'recipe_short_link', args=[pk]))})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UsersViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserReadSerializer
    permission_classes = [AllowAny]

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = (
            User.objects
            .filter(authors__user=request.user)
            .annotate(recipes_count=Count('recipes', distinct=True))
            .distinct()
        )
        page = self.paginate_queryset(authors)
        serializer = SubscriptionAuthorSerializer(
            page or authors,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user

        if request.method == 'DELETE':
            get_object_or_404(
                Follow, user_id=user.id, following_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if user.id == id:
            raise ValidationError({
                'errors': f'Нельзя подписаться на самого себя '
                          f'(@{user.username}).'
            })
        author = get_object_or_404(User, pk=id)
        _, created = Follow.objects.get_or_create(user_id=user.id,
                                                  following_id=author.id)
        if not created:
            raise ValidationError({
                'errors': f'Вы уже подписаны на этого автора '
                          f'(@{author.username}).'
            })
        return Response(
            SubscriptionAuthorSerializer(
                author,
                context={'request': request})
            .data,
            status=status.HTTP_201_CREATED)

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
