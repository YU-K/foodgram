from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Пользователь',
        help_text='Пользователь, добавивший рецепт в корзину',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_carts',
        verbose_name='Рецепт',
        help_text='Рецепт, добавленный в корзину',
    )

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_item',
            )
        ]

    def __str__(self):
        return f'{self.user} 🛒 {self.recipe}'

