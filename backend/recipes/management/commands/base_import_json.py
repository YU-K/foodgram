import json
from typing import Iterable

from django.core.management.base import BaseCommand, CommandError


class BaseJsonImportCommand(BaseCommand):
    """
    Базовая команда импорта: читает JSON-массив объектов и делает bulk_create.
    Наследники должны определить:
      - model: Django-модель
      - help: строку помощи (опционально)
      - ignore_conflicts: True/False (по умолчанию True)
    При необходимости можно переопределить:
      - build_instance(self, item: dict) -> model
    """
    model = None
    ignore_conflicts: bool = True
    file_arg_name: str = 'file_path'

    def add_arguments(self, parser):
        parser.add_argument(
            self.file_arg_name,
            type=str,
            help='Путь к JSON-файлу с данными (массив объектов)',
        )

    def build_instance(self, item: dict):
        """Преобразование словаря в инстанс модели."""
        if self.model is None:
            raise CommandError("Не задана модель (атрибут 'model').")
        return self.model(**item)

    def _load_items(self, file_path: str) -> Iterable[dict]:
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise CommandError(f'Файл не найден: {file_path}') from e
        except json.JSONDecodeError as e:
            raise CommandError(f'Некорректный JSON: {e}') from e

        if not isinstance(data, list):
            raise CommandError('Ожидался JSON-массив объектов.')

        return data

    def handle(self, *args, **options):
        file_path = options[self.file_arg_name]
        items = self._load_items(file_path)

        try:
            created_count = len(
                self.model.objects.bulk_create(
                    [self.build_instance(item) for item in items],
                    ignore_conflicts=self.ignore_conflicts,
                )
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Ошибка при импорте из файла '{file_path}' "
                    f"({type(e).__name__}): {e}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Импортировано {created_count} записей "
                f"(источник: {file_path}, модель: {self.model.__name__}, "
                f"ignore_conflicts={self.ignore_conflicts})"
            )
        )
