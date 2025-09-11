import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

BLACK = '#000000'
NONE = ''
COLOR_CHOICES = [
    (BLACK, 'Чёрный'),
    (NONE, 'Без цвета'),
]


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        blank=False,
        verbose_name='Название тега',
        help_text='Введите название тега (например: Завтрак, Обед, Ужин)',
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=False,
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
        max_length=255,
        blank=False,
        verbose_name='Название',
        help_text='Введите название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=50,
        blank=False,
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
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        null=False,
        blank=False,
        verbose_name='Автор',
        help_text='Автор рецепта',
    )
    name = models.CharField(
        max_length=255,
        blank=False,
        verbose_name='Название',
        help_text='Введите название рецепта',
    )
    text = models.TextField(
        blank=False,
        verbose_name='Описание',
        help_text='Подробное описание рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        blank=False,
        verbose_name='Изображение',
        help_text='Загрузите изображение готового блюда',
    )
    cooking_time = models.PositiveIntegerField(
        help_text='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1,
                message='Минимальное время приготовления - 1 минута.'
            )
        ],
        blank=False,
        verbose_name='Время приготовления',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        blank=False,
        verbose_name='Теги',
        help_text='Выберите один или несколько тегов для рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        blank=False,
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты и укажите их количество',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    short_link = models.SlugField(
        max_length=16,
        unique=True,
        blank=True,
        verbose_name='Короткая ссылка',
        help_text='Постоянный код для короткой ссылки',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        if not self.short_link:
            while True:
                code = uuid.uuid4().hex[:8]
                if not Recipe.objects.filter(short_link=code).exists():
                    self.short_link = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Выберите рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        help_text='Выберите ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        help_text='Количество ингредиента',
        validators=[
            MinValueValidator(
                1,
                message='Минимальное количество — 1'
            )
        ],
        blank=False,
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self):
        return f'{self.ingredient} x {self.amount} для {self.recipe}'


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Выберите рецепт',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
        help_text='Выберите тег',
    )

    class Meta:
        verbose_name = 'Тег в рецепте'
        verbose_name_plural = 'Теги в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='unique_recipe_tag',
            )
        ]

    def __str__(self):
        return f'{self.recipe} - {self.tag}'
