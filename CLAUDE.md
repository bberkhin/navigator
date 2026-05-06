# CLAUDE.md — Региональный навигатор мер господдержки
> Этот файл читается Claude Code при каждом запуске. Содержит всё необходимое для работы с проектом.

---

## Что за проект

Веб-портал «Региональный навигатор мер господдержки» — цифровая платформа для предприятий станкоинструментальной отрасли Новосибирской области. Помогает найти подходящую программу господдержки, подготовить заявку и записаться на консультацию к эксперту.

**Оператор:** НГТУ · Центр НТР станкостроения  
**Аудитория:** производители станков, ретрофитчики, МСП, институты поддержки (Минпромторг НСО, ТПП НСО)

---

## Технологический стек

| Слой | Технология |
|------|-----------|
| Фреймворк | Django 5.x (Python 3.12) |
| Шаблоны + интерактивность | Django Templates + HTMX |
| База данных | PostgreSQL 16 + pgvector |
| ORM + миграции | Django ORM (`manage.py makemigrations / migrate`) |
| Авторизация | django-allauth + VK ID (OAuth 2.0) |
| AI / RAG | LangChain + GigaChat SDK + pgvector |
| Контент программ | YAML-файлы в `content/programs/` |
| Редактор контента | Кастомная страница `/cms` на Django |
| Adminка | Django Admin (только транзакционные данные) |
| Карта | 2GIS Maps JS API |
| Уведомления | SMTP email + VK Bot API (Max) |
| Деплой | gunicorn + nginx + supervisor (VPS Linux) |

---

## Структура проекта

```
navigator/                     # корень проекта
├── CLAUDE.md                  # этот файл
├── manage.py
├── requirements.txt
├── .env                       # секреты — никогда не коммитить
├── .gitignore
│
├── config/                    # настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── content/                   # контент в файлах (git-версионирование)
│   ├── programs/              # YAML-карточки программ поддержки
│   │   └── frp-stankostroyenie.yaml
│   ├── articles/              # Markdown-обзоры, кейсы, пособия
│   └── templates_meta/        # метаданные шаблонов и чек-листов
│
├── apps/
│   ├── catalog/               # каталог программ — чтение YAML, фильтрация
│   ├── navigator/             # анкета-классификатор, eligibility-checker
│   ├── library/               # библиотека материалов
│   ├── consult/               # консультации, слоты, запись
│   ├── cms/                   # редактор /cms для эксперта
│   ├── ai/                    # GigaChat RAG, AI-консультант
│   ├── map/                   # 2GIS интеграция
│   └── accounts/              # авторизация VK ID, роли, личный кабинет
│
├── templates/                 # Django HTML-шаблоны
│   ├── base.html
│   ├── catalog/
│   ├── navigator/
│   ├── library/
│   ├── consult/
│   ├── cms/
│   └── map/
│
└── static/                    # CSS, JS, изображения
```

---

## Команды

```bash
# Разработка
python manage.py runserver          # запуск dev-сервера на localhost:8000
python manage.py shell              # Django shell

# База данных
python manage.py makemigrations     # создать миграции после изменения моделей
python manage.py migrate            # применить миграции
python manage.py createsuperuser    # создать admin-пользователя

# Статика
python manage.py collectstatic      # собрать статику для продакшна

# Зависимости
pip install -r requirements.txt
pip freeze > requirements.txt       # после добавления новых пакетов
```

---

## Переменные окружения (.env)

```env
DEBUG=True
SECRET_KEY=...
DATABASE_URL=postgresql://navigator:пароль@localhost:5432/navigator_db
VK_CLIENT_ID=...
VK_CLIENT_SECRET=...
GIGACHAT_AUTH_KEY=...
TWOGIS_API_KEY=...
EMAIL_HOST=...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
GIT_AUTHOR_NAME=...          # для коммитов из /cms
GIT_AUTHOR_EMAIL=...
```

---

## Соглашения по коду

**Именование:**
- Приложения Django — строчные: `catalog`, `navigator`, `consult`
- Классы моделей — PascalCase: `Consultation`, `Slot`, `AiLog`
- URL-имена — kebab-case через namespace: `catalog:detail`, `consult:book`
- Шаблоны — `apps/имя_приложения/templates/имя_приложения/страница.html`
- YAML-файлы программ — kebab-case slug: `frp-stankostroyenie.yaml`

**Язык:**
- Все тексты интерфейса — русский
- Комментарии в коде — русский единообразно в файле
- Поля моделей и переменные — английские

**HTMX:**
- HTMX-фрагменты возвращаются из отдельных view с суффиксом `_partial`
- Пример: `navigator_step_partial(request)` возвращает только HTML-фрагмент следующего шага
- Атрибут `hx-swap="innerHTML"` — основной режим вставки

**YAML и контент:**
- Связь с программой из БД — через поле `program_slug` (текст), не FK
- Поле `verified_at` обязательное — без него карточка не сохраняется
- Допустимые значения `support_form`: `loan`, `subsidy`, `grant`, `tax`
- Допустимые значения `relevance`: `high`, `medium`, `low`

---

## Модели данных (PostgreSQL)

```python
# apps/accounts/models.py
class User(AbstractUser):
    role = models.CharField(choices=['user','expert','admin'], default='user')
    vk_id = models.CharField(max_length=50, blank=True)

# apps/consult/models.py
class Slot(models.Model):
    expert = models.ForeignKey(User, ...)
    datetime = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

class Consultation(models.Model):
    user = models.ForeignKey(User, ...)
    slot = models.ForeignKey(Slot, ...)
    program_slug = models.CharField(max_length=100)   # ссылка на YAML
    request_type = models.CharField(choices=['consult','review'])
    description = models.TextField()
    status = models.CharField(choices=['new','scheduled','done'])
    expert_notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)

# apps/ai/models.py
class AiLog(models.Model):
    user = models.ForeignKey(User, null=True, ...)    # null для анонимных
    prompt_hash = models.CharField(max_length=64)
    response_hash = models.CharField(max_length=64)
    program_slugs = models.JSONField(default=list)    # какие программы были в контексте
    created_at = models.DateTimeField(auto_now_add=True)

# apps/navigator/models.py
class NavigatorSession(models.Model):
    user = models.ForeignKey(User, null=True, ...)    # null для анонимных
    answers = models.JSONField()
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Структура YAML-карточки программы

```yaml
# content/programs/frp-stankostroyenie.yaml
title: "ФРП · Станкостроение"
slug: frp-stankostroyenie
admin_org: "Фонд развития промышленности"
legal_basis: "Постановление Правительства РФ №..."
support_form: loan          # loan | subsidy | grant | tax
min_amount_mln: 50
max_amount_mln: 500
rate_percent: 5
term: "до 7 лет"
okveds:
  - "28.41"
  - "28.49"
  - "25.73"
project_stage: production   # rd | pilot | production | scale | modernization
enterprise_profile: "МСП и крупные, наличие НИОКР необязательно"
relevance: high             # high | medium | low
verified_at: ГГГГ-ММ-ДД
verified_by: "Иванов А.П."
deadline_at: ГГГГ-ММ-ДД    # null если нет фиксированного дедлайна
official_url: "https://frprf.ru/..."
typical_errors:
  - "Некорректный ОКВЭД в ГИСП"
  - "Недостаточное ТЭО"
  - "Отсутствие подтверждения локализации"
center_notes: "Для ретрофитчиков — см. программу Комплектующие изделия"
```

---

## Ключевые роуты

| URL | Приложение | Назначение |
|-----|-----------|-----------|
| `/` | config | Главная страница |
| `/catalog/` | catalog | Список программ с фильтрами |
| `/catalog/<slug>/` | catalog | Карточка программы |
| `/catalog/compare/` | catalog | Сравнение до 3 программ |
| `/navigator/` | navigator | Анкета-классификатор |
| `/navigator/step/` | navigator | HTMX — следующий шаг анкеты |
| `/navigator/check/` | navigator | HTMX — eligibility-checker |
| `/navigator/result/` | navigator | Результат подбора программ |
| `/library/` | library | Список материалов |
| `/library/<slug>/` | library | Карточка материала |
| `/consult/` | consult | Форма записи на консультацию |
| `/consult/slots/` | consult | HTMX — доступные слоты |
| `/account/` | accounts | Личный кабинет |
| `/map/` | map | Карта экосистемы (2ГИС) |
| `/cms/` | cms | Редактор контента для эксперта |
| `/cms/programs/` | cms | Список программ в редакторе |
| `/cms/programs/<slug>/edit/` | cms | Форма редактирования карточки |
| `/api/ai/chat/` | ai | AI-консультант (GigaChat RAG) |
| `/api/map/objects/` | map | Объекты карты (JSON) |
| `/admin/` | Django Admin | Только транзакционные данные |

---

## Логика /cms — редактор YAML для эксперта

Страница `/cms` — это кастомный Django-интерфейс для эксперта-аналитика. Не Django Admin — отдельное приложение `cms`.

**Как работает сохранение:**
1. Эксперт открывает `/cms/programs/<slug>/edit/`
2. Django читает YAML-файл → заполняет форму
3. Эксперт редактирует поля → нажимает «Сохранить»
4. Django валидирует форму (verified_at обязателен, support_form — enum)
5. Django сериализует данные → пишет YAML-файл на диск
6. Django делает `git commit` с сообщением «Обновлена программа: <title>, <автор>»
7. Редирект на список с сообщением об успехе

**Защита:** `/cms/*` защищён декоратором `@role_required('expert', 'admin')`.

---

## Логика AI-консультанта (RAG)

```
Запрос пользователя
    ↓
POST /api/ai/chat/
    ↓
Django view → LangChain
    ↓
1. Embedding запроса (GigaChat embeddings)
2. Векторный поиск в pgvector по таблице program_chunks
3. Топ-5 релевантных чанков из YAML-файлов
    ↓
4. Формирование промпта: контекст + вопрос
5. Запрос к GigaChat API
    ↓
6. Постпроцессинг: добавить дисклеймер, ссылки на программы
7. Логирование в AiLog
    ↓
Ответ с цитатами и дисклеймером
```

**Важно:** ответы строятся только из верифицированных YAML-файлов. Галлюцинации за пределами базы — недопустимы. Дисклеймер обязателен в каждом ответе.

---

## Eligibility-checker

Проверяет критические несоответствия до завершения анкеты. Вызывается HTMX на шаге 2 (ОКВЭД) и шаге 3 (размер предприятия).

```python
# Возвращает:
{
    "blockers": [
        {"field": "okveds", "message": "ОКВЭД 47.11 не входит в допустимые для этой программы"}
    ],
    "warnings": [
        {"field": "revenue", "message": "Выручка на границе требований — уточните у эксперта"}
    ]
}
```

Если есть `blockers` — программа исключается из результатов. Если только `warnings` — показывается с флагом «требует уточнения».

---

## Безопасность и 152-ФЗ

- Персональные данные хранятся только на серверах НГТУ
- Загруженные документы предприятий — вне web root, доступ только через signed URL (TTL 15 мин)
- AI-логи хранятся в PostgreSQL обязательно (требование 152-ФЗ)
- Rate limiting на `/api/ai/chat/` — не более 20 запросов в минуту на пользователя
- CSRF-защита Django включена везде
- `.env` никогда не попадает в git

---

## Типичные задачи — как формулировать

При постановке задачи Claude Code всегда указывай:

**Контекст:** какой модуль, какой файл затрагивается  
**Данные:** из YAML или из БД  
**Интерактивность:** нужен ли HTMX-запрос или это статичная страница  
**Доступ:** какая роль пользователя

**Примеры хороших задач:**
```
"В apps/catalog/views.py добавь фильтрацию по полю support_form.
Фильтр передаётся как GET-параметр ?type=loan.
Данные берутся из YAML-файлов в content/programs/.
Результат возвращается как HTMX-фрагмент в catalog/programs_list.html"

"Создай модель Consultation в apps/consult/models.py
согласно схеме из CLAUDE.md. Добавь миграцию.
Зарегистрируй модель в Django Admin."

"В apps/cms/views.py реализуй сохранение YAML-файла программы.
После записи файла сделай git commit через subprocess.
Автор коммита — из settings.GIT_AUTHOR_NAME"
```

---

## Что НЕ делать

- Не хранить программы поддержки в PostgreSQL — только YAML-файлы
- Не использовать FK на программы из БД — только поле `program_slug` (текст)
- Не коммитить `.env` в git
- Не отвечать из AI без дисклеймера
- Не давать доступ к `/cms` без проверки роли
- Не раздавать загруженные документы по прямой ссылке — только signed URL
- Не писать inline-стили в шаблонах — только классы через static CSS
