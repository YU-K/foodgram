import json

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт данных из JSON в таблицу Ingredient'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу с данными'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                ingredients = [Ingredient(**item) for item in data]

                Ingredient.objects.bulk_create(
                    ingredients,
                    ignore_conflicts=True,
                )
            self.stdout.write(self.style.SUCCESS(
                f'Импортировано {len(ingredients)} новых записей'))
        except Exception as e:
            raise CommandError(f'Ошибка при импорте ({type(e).__name__}): {e}')
