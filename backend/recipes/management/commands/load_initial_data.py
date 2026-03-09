from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Загрузка стартовых данных'

    def handle(self, *args, **kwargs):
        call_command('import_tags', '/app/data/tags.json')
        call_command('import_ingredients', '/app/data/ingredients.json')
        self.stdout.write(self.style.SUCCESS('Стартовые данные загружены'))