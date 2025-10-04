![Build Status](https://github.com/YU-K/foodgram/actions/workflows/main.yml/badge.svg?branch=main)
#### Сайт проекта: [https://foodgram-site.ddns.net/](https://foodgram-site.ddns.net/)


# FOODGRAM

**FOODGRAM** — это веб-приложение для публикации и обмена рецептами.  
Пользователи могут добавлять собственные рецепты, сохранять понравившиеся, формировать список покупок и подписываться на других авторов.  

---

## Возможности
- Регистрация и авторизация пользователей
- Добавление, редактирование и удаление рецептов
- Загрузка фотографий к рецептам
- Подписки на других пользователей
- Список избранного
- Формирование списка покупок по выбранным рецептам
- Административная панель

---

## Технологии
- **Backend**: Python, Django, Django REST Framework
- **Frontend**: React
- **База данных**: PostgreSQL
- **Контейнеризация**: Docker, Docker Compose
- **Веб-сервер**: Nginx, Gunicorn
- **CI/CD**: GitHub Actions (опционально)

---

## Установка и запуск

### 1. Клонировать репозиторий
```bash
git clone https://github.com/YU-K/foodgram.git
cd foodgram
```
### 2. Запуск в Docker
```bash
sudo docker compose -f docker-compose_production.yml up -d
```
### 3. Применить миграции и собрать статику
```bash
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py collectstatic --noinput
```
### 4. Создать суперпользователя
```bash
sudo docker compose exec backend python manage.py createsuperuser
```
### 5. Импорт ингредиентов (JSON-массив объектов)
```bash
sudo docker compose exec backend python manage.py import_ingredients data/ingredients.json
```
### 6 Импорт тегов (JSON-массив объектов)
```bash
sudo docker compose exec backend python manage.py import_tags data/tags.json
```
## Доступы

- [Сайт проекта](https://foodgram-site.ddns.net/)
- [Админка](https://foodgram-site.ddns.net/admin/)
- [API docs (Swagger)](https://foodgram-site.ddns.net/api/docs/)
- [API docs (ReDoc)](https://foodgram-site.ddns.net/redoc/)


### Автор проекта

- **ФИО:** Катков Юрий  
- [GitHub](https://github.com/YU-K)
- [Email](mailto:katkov_@mail.ru)

