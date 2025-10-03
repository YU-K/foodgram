import django_filters
from django.contrib import admin
from django.db.models import Case, IntegerField, Q, When
from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.CharFilter(method='filter_tags')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(self, recipes, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return recipes.filter(tags__slug__in=tags).distinct()
        return recipes

    def filter_is_favorited(self, recipes, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return recipes.filter(favorites__user=user)
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            return recipes.filter(in_carts__user=user)
        return recipes


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, ingredients, name, value):
        return ingredients.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).order_by(

            Case(
                When(name__istartswith=value, then=0),
                default=1,
                output_field=IntegerField()
            )
        )


class HasRecipesFilter(admin.SimpleListFilter):
    title = "есть рецепты"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "есть подписки"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscriptions__isnull=True)
        return queryset


class HasFollowersFilter(admin.SimpleListFilter):
    title = "есть подписчики"
    parameter_name = "has_followers"

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscribers__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscribers__isnull=True)
        return queryset
