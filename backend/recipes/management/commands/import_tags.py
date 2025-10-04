from .base_import_json import BaseJsonImportCommand
from recipes.models import Tag


class Command(BaseJsonImportCommand):
    help = 'Импорт тегов из JSON в таблицу Tag'
    model = Tag
