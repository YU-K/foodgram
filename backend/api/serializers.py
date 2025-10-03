from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers

MAX_COOKING_TIME = 1440
MIN_COOKING_TIME = 1
MIN_INGREDIENT_AMOUNT = 1

User = get_user_model()


class UserReadSerializer(DjoserUserSerializer):
    """Информация о пользователе."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        user = getattr(self.context.get('request'), 'user', None)
        return bool(
            user
            and user.is_authenticated
            and Follow.objects.filter(user_id=user.id,
                                      following_id=obj.id).exists()
        )

    def create(self, validated_data):
        raise serializers.ValidationError('Этот сериализатор '
                                          'только для чтения.')

    def update(self, instance, validated_data):
        raise serializers.ValidationError('Этот сериализатор '
                                          'только для чтения.')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.ReadOnlyField()


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients', 'pub_date',
            'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=recipe).exists()


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image',
            'cooking_time', 'tags', 'ingredients',
        )

    def validate_ingredients(self, ingredients):
        seen = set()
        duplicates = []
        for item in ingredients:
            ing = item['ingredient']
            if ing.id in seen:
                duplicates.append(ing.name)
            else:
                seen.add(ing.id)
        if duplicates:
            raise serializers.ValidationError(
                {'ingredients': f'Дублируются: '
                                f'{", ".join(sorted(set(duplicates)))}'})
        return ingredients

    def save_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients
        ])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create({
            **validated_data,
            'author': self.context['request'].user
        })
        recipe.tags.add(*tags)
        self.save_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.save_ingredients(ingredients, instance)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецептов в подписках."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionAuthorSerializer(UserReadSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(UserReadSerializer.Meta):
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'recipes', 'recipes_count', 'is_subscribed', 'avatar')
        read_only_fields = fields

    def get_recipes(self, obj):
        req = self.context.get('request')
        raw = req.query_params.get('recipes_limit') if req else None
        try:
            limit = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            limit = None

        qs = obj.recipes.all().order_by('id')
        if limit is not None and limit >= 0:
            qs = qs[:limit]
        return RecipeShortSerializer(qs, many=True,
                                     context={'request': req}).data

    def create(self, *args, **kwargs):
        raise serializers.ValidationError('Этот сериализатор '
                                          'только для чтения.')

    def update(self, *args, **kwargs):
        raise serializers.ValidationError('Этот сериализатор '
                                          'только для чтения.')


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
