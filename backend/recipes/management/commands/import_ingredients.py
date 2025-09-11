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
        except FileNotFoundError:
            raise CommandError(f'Файл {file_path} не найден')
        except json.JSONDecodeError as e:
            raise CommandError(f'Ошибка чтения JSON: {e}')

        if not isinstance(data, list):
            raise CommandError('JSON должен содержать список объектов')

        created_count = 0
        for item in data:
            obj, created = Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Импортировано {created_count} новых записей'
        ))
