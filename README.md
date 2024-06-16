# Foodgram

[Foodgram](https://foodgrammm.ru/) - Блог для публикации рецептов, с возможностью добавления в избранное,
подписками на авторов и выгрузкой списка покупок.
Для публикации необходима регистрация.

![foodrgam](https://github.com/Naoidei/foodgram/actions/workflows/main.yml/badge.svg)

## API

Спецификация к API расположена по адресу :
https://foodgrammm.ru/api/docs/redoc.html

## Деплой

Чтобы задеплоить проект, скопируйте на сервер в целевую директорию файл docker-compose.production.yml и последовательно выполните команды:

```
sudo docker compose -f docker-compose.production.yml up
```

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```

```
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```


## Переменные окружения

Для развертывания проекта необходимо разместить на сервере файл .env и добавить в него следующие переменные окружения:

`POSTGRES_DB`

`POSTGRES_USER`

`POSTGRES_PASSWORD`

`DB_HOST`

`DB_PORT`

`DJANGO_SECRET_KEY`

`DJANGO_DEBUG`

`DJANGO_ALLOWED_HOSTS`



## Стек технологий

- Python
- Django
- DRF
- Nginx
- Docker
- JavaScript



## Автор

- Игорь Михайлищук (Naoidei)
