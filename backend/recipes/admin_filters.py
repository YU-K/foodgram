from django.contrib import admin


class BaseYesNoFilter(admin.SimpleListFilter):
    """Базовый фильтр с вариантами 'Да' и 'Нет'."""

    title = 'есть связи'
    parameter_name = 'has_related'
    related_name: str | None = None
    use_distinct: bool = True
    LOOKUPS = (('yes', 'Да'), ('no', 'Нет'))

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def filter_yes(self, queryset):
        qs = queryset.filter(**{f'{self.related_name}__isnull': False})
        return qs.distinct() if self.use_distinct else qs

    def filter_no(self, queryset):
        qs = queryset.filter(**{f'{self.related_name}__isnull': True})
        return qs.distinct() if self.use_distinct else qs

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return self.filter_yes(queryset)
        if value == 'no':
            return self.filter_no(queryset)
        return queryset


class InRecipesFilter(BaseYesNoFilter):
    title = 'используется в рецептах'
    parameter_name = 'in_recipes'
    related_name = 'recipes'


class CookingTimeFilter(BaseYesNoFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)

        times = list(
            recipes.order_by('cooking_time').values_list('cooking_time',
                                                         flat=True)
        )
        if len(set(times)) < 3:
            return []

        n = times[len(times) // 3]
        m = times[2 * len(times) // 3]
        tmin, tmax = times[0], times[-1]

        self._ranges = {
            'fast': (tmin, n),
            'medium': (n + 1, m),
            'long': (m + 1, tmax),
        }

        fast_count = self._filtered(recipes, 'fast').count()
        medium_count = self._filtered(recipes, 'medium').count()
        long_count = self._filtered(recipes, 'long').count()

        return [
            ('fast', f'быстрее {n} мин ({fast_count})'),
            ('medium', f'быстрее {m} мин ({medium_count})'),
            ('long', f'долго ({long_count})'),
        ]

    def queryset(self, request, recipes):
        val = self.value()
        if not val or val not in self._ranges:
            return recipes
        return self._filtered(recipes, val)

    def _filtered(self, recipes, key: str):
        return recipes.filter(cooking_time__range=self._ranges[key])


class HasRecipesFilter(BaseYesNoFilter):
    title = 'есть рецепты'
    parameter_name = 'has_recipes'
    related_name = 'recipes'


class HasSubscriptionsFilter(BaseYesNoFilter):
    title = 'есть подписки'
    parameter_name = 'has_subscriptions'
    related_name = 'subscriptions'


class HasFollowersFilter(BaseYesNoFilter):
    title = 'есть подписчики'
    parameter_name = 'has_followers'
    related_name = 'authors'
