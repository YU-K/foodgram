from rest_framework import serializers

from .models import Recipe


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецептов в подписках."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
