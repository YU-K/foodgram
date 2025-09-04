from rest_framework import serializers

from .models import Recipe, Tag, Ingredient, RecipeIngredient, RecipeTag
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


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

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients', 'pub_date',
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    ingredient = serializers.PrimaryKeyRelatedField(
        queryset = Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients',
        )

    def create_ingredients(self, ingredients, recipe):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create_tags(self, tags, recipe):
        objs = [
            RecipeTag(recipe=recipe, tag=tag)
            for tag in tags
        ]
        RecipeTag.objects.bulk_create(objs)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        RecipeTag.objects.filter(recipe=instance).delete()
        self.create_tags(tags, instance)

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


