from .base_import_json import BaseJsonImportCommand
from recipes.models import Ingredient


class Command(BaseJsonImportCommand):
    help = 'Импорт продуктов из JSON в таблицу Ingredient'
    model = Ingredient
