from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    UserChangeForm,
    UserCreationForm,
)
from django.db.models import Count
from django.utils.safestring import mark_safe

from .admin_filters import (
    CookingTimeFilter,
    HasFollowersFilter,
    HasRecipesFilter,
    HasSubscriptionsFilter,
    InRecipesFilter,
)
from .models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

User = get_user_model()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipesCountMixin:
    @admin.display(description='Рецепты')
    def recipes_count(self, obj):
        return obj.recipes.count()


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'avatar')


class UserUpdateForm(UserChangeForm):
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

    @admin.display(description='Продукты')
    def ingredients_list(self, recipe):
        return mark_safe(
            '<br>'.join((f'{ri.ingredient.name} — '
                         f'{ri.amount} {ri.ingredient.measurement_unit}')
                        for ri in recipe.recipe_ingredients.all()))

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return mark_safe(
            '<br>'.join((f'{tag.name}'
                        for tag in recipe.tags.all())))

    @admin.display(description='Изображение')
    def image_preview(self, recipe):
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" width="80" '
                f'height="80" style="object-fit: cover;" />')
        return '—'


@admin.register(Favorite, ShoppingCart)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreateForm
    form = UserUpdateForm
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
        ('Credentials', {'fields': ('email', 'password')}),
        ('Personal info',
            {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        ('Permissions',
            {'fields': ('is_active', 'is_staff', 'is_superuser',
                        'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        ('Credentials',
         {'classes': ('wide',), 'fields': ('email', 'password1',
                                           'password2')}),
        ('Personal info',
         {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        ('Permissions',
         {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                     'user_permissions')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            recipes_count=Count('recipes', distinct=True),
            subscriptions_count=Count('subscriptions',
                                      distinct=True),
            followers_count=Count('authors', distinct=True),
        )

    @admin.display(description='ФИО')
    def full_name(self, user):
        full = f'{user.first_name} {user.last_name}'.strip()
        return full or '—'

    @admin.display(description='Аватар')
    def avatar_thumb(self, user):
        if getattr(user, 'avatar', None):
            return mark_safe(
                f'<img src="{user.avatar.url}" width="40" height="40" '
                f'style="border-radius:50%;object-fit:cover;" />')
        return '—'

    @admin.display(ordering='recipes_count', description='Рецептов')
    def recipes_total(self, user):
        return user.recipes_count

    @admin.display(ordering='subscriptions_count', description='Подписок')
    def subscriptions_total(self, user):
        return user.subscriptions_count

    @admin.display(ordering='followers_count', description='Подписчиков')
    def followers_total(self, user):
        return user.followers_count


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
