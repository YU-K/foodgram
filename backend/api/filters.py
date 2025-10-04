import django_filters as filters
from django.db.models import Case, IntegerField, Q, Value, When

from recipes.models import Ingredient, Recipe, Tag


def _to_bool(v):
    if v is None:
        return None
    s = str(v).lower()
    if s in ('1', 'true', 't', 'yes', 'y'):
        return True
    if s in ('0', 'false', 'f', 'no', 'n'):
        return False
    return None


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.TypedChoiceFilter(
        choices=(('1', '1'), ('0', '0')),
        coerce=_to_bool,
        method='filter_is_favorited',
    )
    is_in_shopping_cart = filters.TypedChoiceFilter(
        choices=(('1', '1'), ('0', '0')),
        coerce=_to_bool,
        method='filter_is_in_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, qs, name, value):
        if value is None:
            return qs
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:

            return qs.none() if value else qs
        return qs.filter(favorites__user_id=user.id) if value else (
            qs.exclude(favorites__user_id=user.id))

    def filter_is_in_cart(self, qs, name, value):
        if value is None:
            return qs
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return qs.none() if value else qs
        return qs.filter(in_carts__user_id=user.id) if value else (
            qs.exclude(in_carts__user_id=user.id))


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_by_query')
    search = filters.CharFilter(method='filter_by_query')

    class Meta:
        model = Ingredient
        fields = ('name', 'search')

    def filter_by_query(self, qs, _field, value):
        q = (value or '').strip()
        if not q:
            return qs
        return qs.filter(
            Q(name__istartswith=q) | Q(name__icontains=q)
        ).order_by(
            Case(
                When(name__istartswith=q, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            'name',
        )
