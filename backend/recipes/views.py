import os

from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def recipe_short_link(request, recipe_id):
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f"Рецепт с id={recipe_id} не найден")
    return redirect(
        f"{os.getenv('FRONTEND_URL', 'http://localhost')}/recipes/{recipe_id}/"
    )
