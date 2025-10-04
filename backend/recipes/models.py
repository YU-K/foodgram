from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    RegexValidator,
)
from django.db import models

MIN_COOKING_TIME = 1
MIN_INGREDIENT_AMOUNT = 1
USERNAME_REGEX = RegexValidator(
    regex=r"^[\w.@+-]+\Z",
    message="Допустимы только буквы, цифры и символы @ . + - _",
)


class User(AbstractUser):
    username = models.CharField(
        'Ник',
        max_length=150,
        unique=True,
        validators=(USERNAME_REGEX,),
        help_text='Только буквы, цифры и @/./+/-/_',
    )
    email = models.EmailField(
        'Email',
        max_length=254,
        unique=True,
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('email',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название',
        help_text='Введите название тега (например: Завтрак, Обед, Ужин)',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Слаг',
        help_text='Введите уникальный слаг для тега (латиница, без пробелов)',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
        help_text='Введите название продукта',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
        help_text='Например: грамм, мл, штука',
    )

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            )
        ]
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Автор',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Введите название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Подробное описание рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение',
        help_text='Загрузите изображение готового блюда',
    )
    cooking_time = models.PositiveIntegerField(
        help_text='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f'Минимальное время приготовления - {MIN_COOKING_TIME}'
                        f' минута.'
            )
        ],
        verbose_name='Время приготовления (мин.)',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Выберите один или несколько тегов для рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Продукты',
        help_text='Выберите продукты и укажите их количество',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Выберите рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
        help_text='Выберите продукт',
    )
    amount = models.PositiveSmallIntegerField(
        help_text='Количество продуктов',
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=f'Минимальное количество — {MIN_INGREDIENT_AMOUNT}'
            )
        ],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецептах'
        default_related_name = 'recipe_ingredients'
        ordering = ('recipe', 'ingredient')
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self):
        return f'{self.ingredient} x {self.amount} для {self.recipe}'


class UserRecipeRelation(models.Model):
    """Базовый класс для Favorite и ShoppingCart."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    action_label: str = 'связал с'

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_user_recipe_unique',
            )
        ]

    def __str__(self):
        return f'{self.user} {self.action_label} {self.recipe}'


class ShoppingCart(UserRecipeRelation):
    action_label = 'добавил в корзину'

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'in_carts'


class Favorite(UserRecipeRelation):
    action_label = 'добавил в избранное'

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'


class Follow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
        help_text='Пользователь, который подписывается',
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор',
        help_text='Пользователь, на которого подписываются',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_follow',
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на  {self.following}'
