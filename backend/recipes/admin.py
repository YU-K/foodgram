from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('name',)




@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count', 'pub_date')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'author')
    inlines = (RecipeIngredientInline,)
    ordering = ('-pub_date',)

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'В избранном'