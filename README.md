# Kittygram

Блог для котиков и их хозяев, с возможностью публикации фото и достижений питомцев.
Для публикации необохдима регистрация.

![kittygram_final](https://github.com/Naoidei/kittygram_final/actions/workflows/main.yml/badge.svg)


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
- Nginx
- Docker
- JavaScript



## Автор

- Игорь Михайлищук (Naoidei)
