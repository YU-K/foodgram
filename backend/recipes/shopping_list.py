from django.db.models import F, Sum
from django.db.models.functions import Coalesce, Lower
from django.utils import timezone

from .models import Recipe, RecipeIngredient


def create_shopping_list_text(user) -> str:
    totals_qs = (
        RecipeIngredient.objects
        .filter(recipe__shoppingcarts__user=user)
        .values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit'),
        )
        .annotate(amount=Coalesce(Sum('amount'), 0))
        .order_by(Lower('name'), Lower('unit'))
    )

    product_lines = [
        (f"{idx}. {item['name'].capitalize()} ({item['unit']}) — "
         f"{item['amount']}")
        for idx, item in enumerate(totals_qs, start=1)
    ]

    recipes = (
        Recipe.objects
        .filter(shoppingcarts__user=user)
        .select_related('author')
        .order_by('name')
        .distinct()
    )

    recipe_lines = [
        f'{idx}. {r.name} — Автор: {r.author}'
        for idx, r in enumerate(recipes, start=1)
    ]

    now_str = timezone.localtime().strftime('%d.%m.%Y %H:%M')
    return '\n'.join([
        f'Список покупок — {now_str}',
        'Продукты:',
        *(product_lines or ['(нет продуктов)']),
        'Рецепты в корзине:',
        *(recipe_lines or ['(нет рецептов)']),
    ])
