from django.db import models
from django.contrib.auth import get_user_model

from ..recipes.models import Recipe

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite',
            )
        ]

    def __str__(self):
        return f'{self.user} ❤️ {self.recipe}'


