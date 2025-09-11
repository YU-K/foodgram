from rest_framework import serializers

from ..recipes.serializers import RecipeSerializer
from .models import ShoppingCart


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe')
