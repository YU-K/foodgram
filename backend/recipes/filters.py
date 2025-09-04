import django_filters
from django_filters import FilterSet

from .models import Recipe


class RecipeFilter(FilterSet):
    tags = django_filters.CharFilter(method='filter_tags')

    class Meta:
        model = Recipe
        fields = ('tags',)

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset
