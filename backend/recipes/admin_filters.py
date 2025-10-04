from django.contrib import admin


class HasRecipesFilter(admin.SimpleListFilter):
    title = "есть рецепты"
    parameter_name = "has_recipes"
    LOOKUPS = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "есть подписки"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscriptions__isnull=True)
        return queryset


class HasFollowersFilter(admin.SimpleListFilter):
    title = "есть подписчики"
    parameter_name = "has_followers"

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(authors__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(authors__isnull=True)
        return queryset
