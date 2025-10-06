import json

from django.core.management.base import BaseCommand, CommandError


class BaseJsonImportCommand(BaseCommand):
    """Импорт JSON-массива объектов в модель."""
    model = None

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу с данными (массив объектов)',
        )

    def handle(self, *args, **options):
        try:
            with open(options['file_path'], encoding='utf-8') as f:
                created_count = len(
                    self.model.objects.bulk_create(
                        (self.model(**item) for item in json.load(f)),
                        ignore_conflicts=True,
                    )
                )
            self.stdout.write(self.style.SUCCESS(
                f"Импортировано {created_count} записей "
                f"(источник: {options['file_path']}, "
                f"модель: {self.model.__name__})"
            ))
        except Exception as e:
            raise CommandError(
                f"Ошибка при импорте из файла '{options['file_path']}' "
                f"({type(e).__name__}): {e}"
            )
