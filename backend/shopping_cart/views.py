from collections import defaultdict

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ..recipes.models import RecipeIngredient
from .models import ShoppingCart


class DownloadShoppingCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user

        cart_items = (
            ShoppingCart.objects.filter(user=user)
                                .select_related('recipe'))
        ingredients = defaultdict(int)

        recipe_ids = [item.recipe.id for item in cart_items]
        recipe_ingredients = (
            RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)
                                    .select_related('ingredient'))

        for ri in recipe_ingredients:
            key = (ri.ingredient.name, ri.ingredient.measurement_unit)
            ingredients[key] += ri.amount

        lines = []
        for (name, unit), total_amount in ingredients.items():
            lines.append(f"{name} ({unit}) — {total_amount}")

        content = "\n".join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response
