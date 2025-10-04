from django.urls import path

from .views import recipe_short_link

urlpatterns = [
    path('s/<int:recipe_id>/', recipe_short_link, name='recipe_short_link'),
]
