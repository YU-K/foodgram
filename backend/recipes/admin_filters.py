from django.contrib import admin


class BaseYesNoFilter(admin.SimpleListFilter):
    """Базовый фильтр с вариантами 'Да' и 'Нет'."""

    LOOKUPS = (('yes', 'Да'), ('no', 'Нет'))

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def filter_yes(self, queryset):
        """Переопределяется в наследниках."""
        return queryset

    def filter_no(self, queryset):
        """Переопределяется в наследниках."""
        return queryset

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return self.filter_yes(queryset)
        if self.value() == 'no':
            return self.filter_no(queryset)
        return queryset


class InRecipesFilter(BaseYesNoFilter):
    title = 'используется в рецептах'
    parameter_name = 'in_recipes'

    def filter_yes(self, qs):
        return qs.filter(recipes__isnull=False).distinct()

    def filter_no(self, qs):
        return qs.filter(recipes__isnull=True)


class CookingTimeFilter(BaseYesNoFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)

        times = list(
            qs.order_by('cooking_time').values_list('cooking_time', flat=True)
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

        fast_count = self._filtered(qs, 'fast').count()
        medium_count = self._filtered(qs, 'medium').count()
        long_count = self._filtered(qs, 'long').count()

        return [
            ('fast', f'быстрее {n} мин ({fast_count})'),
            ('medium', f'быстрее {m} мин ({medium_count})'),
            ('long', f'долго ({long_count})'),
        ]

    def queryset(self, request, recipes):
        val = self.value()
        if not val or not hasattr(self, '_ranges') or val not in self._ranges:
            return recipes
        return self._filtered(recipes, val)

    def _filtered(self, qs, key: str):
        return qs.filter(cooking_time__range=self._ranges[key])


class HasRecipesFilter(BaseYesNoFilter):
    title = "есть рецепты"
    parameter_name = "has_recipes"

    def filter_yes(self, qs):
        return qs.filter(recipes__isnull=False).distinct()

    def filter_no(self, qs):
        return qs.filter(recipes__isnull=True)


class HasSubscriptionsFilter(BaseYesNoFilter):
    title = "есть подписки"
    parameter_name = "has_subscriptions"

    def filter_yes(self, qs):
        return qs.filter(subscriptions__isnull=False).distinct()

    def filter_no(self, qs):
        return qs.filter(subscriptions__isnull=True)


class HasFollowersFilter(BaseYesNoFilter):
    title = "есть подписчики"
    parameter_name = "has_followers"

    def filter_yes(self, qs):
        return qs.filter(authors__isnull=False).distinct()

    def filter_no(self, qs):
        return qs.filter(authors__isnull=True)
