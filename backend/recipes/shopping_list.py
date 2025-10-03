from collections import defaultdict

from django.utils import timezone
from django.utils.text import capfirst

from .models import Recipe


def create_shopping_list_text(user) -> str:
    totals = defaultdict(int)
    recipes = (
        Recipe.objects
        .filter(in_carts__user=user)
        .select_related('author')
        .prefetch_related('recipe_ingredients__ingredient')
        .order_by('name')
        .distinct()
    )
    for r in recipes:
        for ri in r.recipe_ingredients.all():
            name = (ri.ingredient.name or '').strip()
            unit = (ri.ingredient.measurement_unit or '').strip()
            totals[(name, unit)] += int(ri.amount)
    total_items = sorted(
        totals.items(),
        key=lambda kv: (kv[0][0].lower(), kv[0][1].lower())
    )
    product_lines = [
        f'{idx}. {capfirst(name)} ({unit}) — {amount}'
        for idx, ((name, unit), amount) in enumerate(total_items, start=1)
    ]

    def author_display(u):
        return (u.get_full_name() or u.username or u.email)
    recipe_lines = [
        f'{idx}. {r.name} — {author_display(r.author)}'
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
