from django.urls import reverse
from favorites.models import Favorite
from rest_framework import serializers
from shopping_cart.models import ShoppingCart
from users.serializers import Base64ImageField, CustomUserSerializer

from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag


class TagSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source='id', read_only=True)
    label = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'value', 'label')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients', 'pub_date',
            'is_favorited', 'is_in_shopping_cart', 'short_link'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def get_short_link(self, obj):
        request = self.context.get("request")
        path = reverse('recipe_short_link', args=[obj.short_link])
        return request.build_absolute_uri(path)


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients',
        )

    def validate_ingredients(self, value):
        seen = set()
        for item in value:
            ing = item['ingredient']
            if ing.id in seen:
                raise serializers.ValidationError(
                    'Ингредиент указан несколько раз.')
            seen.add(ing.id)
            amount = item.get('amount')
            if amount is None or amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть >= 1.')
        return value

    def create_ingredients(self, ingredients, recipe):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create_tags(self, tags, recipe):
        objs = [
            RecipeTag(recipe=recipe, tag=tag)
            for tag in tags
        ]
        RecipeTag.objects.bulk_create(objs)

    def create(self, validated_data):
        print("validated_data:", validated_data)
        print("CONTENT TYPE:", self.context['request'].content_type)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if tags is not None:
            RecipeTag.objects.filter(recipe=instance).delete()
            self.create_tags(tags, instance)

        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ingredients(ingredients, instance)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data
