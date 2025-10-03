from functools import wraps

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    UserChangeForm,
    UserCreationForm,
)
from django.db.models import Count
from django.utils.safestring import mark_safe as _mark_safe
from django.utils.translation import gettext_lazy as _

from .models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from api.filters import (
    HasFollowersFilter,
    HasRecipesFilter,
    HasSubscriptionsFilter,
)

User = get_user_model()


def mark_safe(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _mark_safe(func(*args, **kwargs))
    return wrapper


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class InRecipesFilter(admin.SimpleListFilter):
    title = 'используется в рецептах'
    parameter_name = 'in_recipes'

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        times = list(qs.values_list('cooking_time', flat=True))

        if not times:
            return []

        times.sort()
        n = times[len(times) // 3]
        m = times[2 * len(times) // 3]

        fast_count = qs.filter(cooking_time__lte=n).count()
        medium_count = (
            qs.filter(cooking_time__gt=n, cooking_time__lte=m).count())
        long_count = qs.filter(cooking_time__gt=m).count()
        return [
            ('fast', f'быстрее {n} мин ({fast_count})'),
            ('medium', f'быстрее {m} мин ({medium_count})'),
            ('long', f'долго ({long_count})'),
        ]

    def queryset(self, request, queryset):
        times = list(queryset.values_list('cooking_time', flat=True))
        if not times:
            return queryset

        times.sort()
        n = times[len(times) // 3]
        m = times[2 * len(times) // 3]

        if self.value() == 'fast':
            return queryset.filter(cooking_time__lte=n)
        if self.value() == 'medium':
            return queryset.filter(cooking_time__gt=n, cooking_time__lte=m)
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=m)
        return queryset


class RecipesCountMixin:
    @admin.display(description='Число рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'avatar')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'avatar',
            'is_active', 'is_staff', 'is_superuser', 'groups',
            'user_permissions',
        )


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', InRecipesFilter)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'favorites_count',
        'ingredients_list',
        'tags_list',
        'image_preview',
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'author', CookingTimeFilter)
    inlines = (RecipeIngredientInline,)
    ordering = ('-pub_date',)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @mark_safe
    @admin.display(description='Продукты')
    def ingredients_list(self, recipe):
        items = [
            f'<li>{ri.ingredient.name}</li>'
            for ri in recipe.recipe_ingredients.all()
        ]
        return f"<ul>{''.join(items)}</ul>"

    @mark_safe
    @admin.display(description='Теги')
    def tags_list(self, recipe):
        items = [f'<li>{tag.name}</li>' for tag in recipe.tags.all()]
        return f"<ul>{''.join(items)}</ul>"

    @mark_safe
    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if recipe.image:
            return (f'<img src="{recipe.image.url}" width="80" '
                    f'height="80" style="object-fit: cover;" />')
        return '—'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        'id', 'username', 'full_name', 'email',
        'avatar_thumb', 'recipes_total', 'subscriptions_total',
        'followers_total', 'is_staff', 'is_active',
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasFollowersFilter,
        "is_staff", "is_superuser", "is_active", "groups",
    )
    ordering = ('last_name', 'first_name', 'username')
    readonly_fields = ('last_login', 'date_joined')
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (_('Credentials'), {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name',
                                         'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (_('Credentials'), {'classes': ('wide',), 'fields': ('email',
                                                             'password1',
                                                             'password2')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name',
                                         'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            recipes_count=Count('recipes', distinct=True),
            subscriptions_count=Count('subscriptions', distinct=True),
            followers_count=Count('subscribers', distinct=True),
        )

    @admin.display(description='ФИО')
    def full_name(self, obj):
        full = f'{obj.first_name} {obj.last_name}'.strip()
        return full or '—'

    @mark_safe
    @admin.display(description='Аватар')
    def avatar_thumb(self, obj):
        if getattr(obj, 'avatar', None):
            return (f'<img src="{obj.avatar.url}" width="40" height="40" '
                    f'style="border-radius:50%;object-fit:cover;" />')
        return '—'

    @admin.display(ordering='recipes_count', description='Рецептов')
    def recipes_total(self, obj):
        return getattr(obj, 'recipes_count', 0)

    @admin.display(ordering='subscriptions_count', description='Подписок')
    def subscriptions_total(self, obj):
        return getattr(obj, 'subscriptions_count', 0)

    @admin.display(ordering='followers_count', description='Подписчиков')
    def followers_total(self, obj):
        return getattr(obj, 'followers_count', 0)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
