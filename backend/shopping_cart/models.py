from django.contrib.auth import get_user_model
from django.db import models

from ..recipes.models import Recipe

User = get_user_model()

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_carts',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_item',
            )
        ]

    def __str__(self):
        return f'{self.user} 🛒 {self.recipe}'

