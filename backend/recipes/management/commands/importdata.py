import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ....recipes.models import Ingredient

User = get_user_model()


class Command(BaseCommand):
    help = 'Импортирует данные из JSON файла в модель ингредиента.'

    def add_arguments(self, parser):
        parser.add_argument('json_file_path', type=str,
                            help='Путь к JSON-файлу с данными.')

    def handle(self, *args, **options):
        json_file = options['json_file_path']
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            Ingredient.objects.bulk_create(Ingredient(**item) for item in data)
