# LinkedIn Profile Validator Service

## Зависимости (пока отсутствет ci/cd):
// Их добавить в проект
1. community_platform\apps\linkedin_verifiercommunityp-440714-40020f08d457.json - креды для broker (google pubsub) (пока запросить в личке у Миши)
2. community_platform\apps\.env - файлик с секретами самого сервиса (пока запросить в личке у Миши)
3. community_platform\config\db.json - креды PostgreSQL (найти значения переменных в Google-секретнице проекта communityp)



## Запуск сервиса локально (IDE or bash)
#### MacOs & Linux Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
#### Setup venv
```bash
cd .\apps\linkedin_verifier\    
uv sync
```
#### Startup
... ide or bash


## Локальный запуск сервиса с использованием Docker
### Сборка Docker-образа
```bash
# Из корня проекта
docker build -t linkedin-verifier:latest -f apps/linkedin_verifier/Dockerfile .
```
### Запуск контейнера
```bash
# Запуск с переменными окружения из .env файла
docker run -p 8000:8000 linkedin-verifier:latest
```
### Проверка работоспособности
```bash
# Проверка статуса сервиса
curl http://localhost:8000/health
```


## "Ручной" деплой в гугл-клауд (TODO: удалить этот пункт как появится ci/cd workflow)
### Сборка Docker-образа
```bash
# Из корня проекта community_platform
docker build -t linkedin-verifier:latest -f apps/linkedin_verifier/Dockerfile .
# Тегирование образа
docker tag linkedin-verifier:latest us-east4-docker.pkg.dev/communityp-440714/linkedin-verifier-repo/linkedin-verifier:latest
# Отправка образа
docker push us-east4-docker.pkg.dev/communityp-440714/linkedin-verifier-repo/linkedin-verifier:latest
```
### Deploy
В гугл клауде -> cloud run


## 
Целевая функция: получать задачи из pubsub на парсинг и парсить + верифицировать профили пользователей.
// pubsub: сейчас sub реализован как push (google) - то есть эндпоинт, в который гугл сам шлет задачу. Поэтому ack, nack - косвенные, по http кодам.

Как вручную поставить задачу на парсинг (localhost:8000 - при необходимости сменить на актуальный):
curl -X POST "http://localhost:8000/tasks/create" -H "Content-Type: application/json" -d "{\"username\": \"pavellukyanov\", \"target_company_label\": \"Yandex\"}"

Как выгрузить спаршенные акки:
```sql
WITH job_history AS (
    SELECT 
        profile_id,
        json_agg(
            json_build_object(
                'company_label', company_label,
                'title', title,
                'description', description,
                'start_date', start_date
            ) ORDER BY start_date DESC
        ) AS job_json,
        array_agg(title ORDER BY start_date DESC) AS titles,
        array_agg(description ORDER BY start_date DESC) AS descriptions
    FROM __test_to_del_alh_community_platform_2.linkedin_experience
    GROUP BY profile_id
)
SELECT 
    a.*,
    jh.job_json,
    -- Последние 5 мест работы
    jh.titles[1] AS title1,    jh.descriptions[1] AS description1,
    jh.titles[2] AS title2,    jh.descriptions[2] AS description2,
    jh.titles[3] AS title3,    jh.descriptions[3] AS description3,
    jh.titles[4] AS title4,    jh.descriptions[4] AS description4,
    jh.titles[5] AS title5,    jh.descriptions[5] AS description5
FROM __test_to_del_alh_community_platform.linkedin_profiles a
LEFT JOIN job_history jh ON a.id = jh.profile_id
WHERE a.parsed_date = CURRENT_DATE;
```
особые указания: Пока что льется в БД Я.посгрес, оттуда забирать:
FROM __test_to_del_alh_community_platform.linkedin_profiles - из этой таблички
WHERE a.parsed_date = CURRENT_DATE; - спаршенное за сегодня выгрузит, их добавть в файлик гуглщшит



## Описание сервиса
Микросервис для валидации профилей LinkedIn. Проверяет опыт работы в целевых компаниях и сохраняет данные профилей.
Пока версия для ручной заливки профилей членов сообщества.
// Для демонстрационного запуска, отладки добавлены mock-данные (и соответсвующий флаг use_mock).


------------------------------------------------------------------------------------------------------------------------
## TODO:

### 1. Валидация опыта работы

**Валидация верификации - валидация опыта работы в легетимных компаниях**
- Продуктовая логика - изучить, реализовать
- ! Оценить результативность автоверификации по сравнению с ручной (уже имеется база)

### 2. Интеграция

**Связь с профилями пользователей**
- Интеграция с основной базой пользователей (флаг верификации, остальные поля - ORMuser?)

**Уведомления для кураторов**
- Система оповещений об изменениях
- Настройка правил уведомлений

### 3. Провайдеры API

**Мониторинг лимитов**
- Предупреждения о лимитах - реализовать через broker (поставить ему задачу)

### 4. Прочее
- LLM генерить описание профиля для дальнейшего использования в мэтчинге
- Где хранить полe is_verified - нужно потом скорее всего для реализации безопасности эндпоинтов гейтвея (на Диме)
- Уточнить, какой логгер юзаем
- Docker + test in minicube + google secrets, конфигурация для облака
- Допроверить различные raise
- Тесты
- Реализовать защищенное использование админского эндпоинта на постановку задач (настроить гугл клауд)
- Врезать постановку задачи на парсинг в user registration flow
- ? для удобства создать поле с источником поставновки задачи/темой - чтобы потом легко выгружать нужные профили
(менеджер поставил для себя - чтобы удобно мог их выгрузить по WHERE)
- ! Перед продом: раскатить на Postgres в гугл клауде (сейчас в Я.облако смотрит)
- ! Перед продом: залить исторические данные + починить баг с записью новых кортежей
- ! Связать ORMUser и ORMLinkedin_profiles (перебирковать внешний ключ) - Дима
- Зарефакторить: убрать все в src
- Добавить установку rust в dockerfile (+ оптимизация по размеру образа + времени сборки(rust для этого же?))
- ! Перепроверить, что все поля верно в пайдентик модели проставлены относительно сырого ответа
- Валидацию аккаунта из задания на парсинг - реализолвать через pydantic (annotaded[valid_func]) (бантик)
------------------------------------------------------------------------------------------------------------------------


## Основные функции

1. **Асинхронная валидация через PubSub - основа сервиса** (`main.py`)
   - Подписка на очередь профилей для валидации
   - Обработка входящих задач
   - Сохранение результатов в БД
   - Обновление лимитов API

2. **Ручной парсинг профилей - вспомогательное** (`parse_profiles.py`)
   - Для обработки списков профилей от комьюнити-менеджеров
   - Пакетная валидация профилей
   - Сохранение результатов в БД (без user_id_fk)

3. **Миграция исторических данных - вспомогательное** (`migrate_profiles.py`)
   - Выгрузка данных из БД в JSON файлы
   - Импорт данных из JSON в новую БД
   - Поддержка разных схем БД
   - Bulk insert с обработкой конфликтов
   - Приведение skills и languages к нижнему регистру
   - Баг: не запишутся новые кортежи - TODO: пофиксить

> **Важно**: Перед импортом данных необходимо очистить целевые таблицы через `TRUNCATE TABLE` с опцией `RESTART IDENTITY`, чтобы избежать конфликтов с sequence для id. Например:
> ```sql
> TRUNCATE TABLE linkedin_profiles, linkedin_education, linkedin_experience RESTART IDENTITY CASCADE;
> ```

## Структура базы данных

### linkedin_profiles
Основная таблица с данными профилей LinkedIn
- Базовая информация (имя, фамилия, URL и т.д.)
- is_open_to_work
- Денормализованные поля текущей работы:
  - `is_currently_employed` - работает ли сейчас
  - `current_jobs_count` - количество текущих мест работы
  - `current_company_label` - название текущей компании
  - `current_position_title` - текущая должность
  - и др.
- Денормализованные поля целевой компании:
  - `is_target_company_found` - найдена ли целевая компания
  - `target_company_positions_count` - количество позиций
  - `target_company_label` - название компании
  - `target_position_title` - последняя должность
  - и др.

### linkedin_experience
История работы
- Связь с профилем (FK)
- Информация о каждой позиции
- Накопительное хранение (новые записи добавляются, старые сохраняются)

### linkedin_education
История образования
- Связь с профилем (FK)
- Информация о каждом месте учебы
- Накопительное хранение

### linkedin_raw_data
Сырые данные от API - чтобы хранить ответы платных сервисов
- `target_linkedin_url` - URL профиля
- `raw_data` - полный ответ API (JSONB)
- `parsed_date` - дата парсинга

### linkedin_api_limits
Лимиты API провайдеров
- Тип провайдера (SCRAPIN/TOMQUIRK)
- Идентификатор провайдера
- Оставшиеся кредиты/запросы
- Время обновления

## Логика работы

1. **Получение задачи**
   - Из PubSub очереди (асинхронно)
   - Из файла с профилями (ручной запуск)

2. **Получение данных**
   - Запрос к API LinkedIn через провайдера
   - Сохранение сырых данных
   - Валидация и преобразование данных

3. **Обработка опыта работы**
   
   a. **Определение текущей работы**
   - Поиск всех позиций без даты окончания
   - Сортировка по дате начала (новые сверху)
   - Выбор самой новой позиции как текущей
   - Сохранение денормализованных полей в профиле
   
   b. **Поиск работы в целевой компании**
   - Case-insensitive поиск по названию компании
   - Сортировка всех найденных позиций по дате
   - Определение последней позиции в компании
   - Проверка, является ли текущей работой
   
   c. **Особенности**
   - Даты хранятся с первым днем месяца (API дает только месяц/год)
   - Для отсутствующих дат используется 1900-01-01
   - Проверяется корректность периодов работы
   - Учитывается возможность нескольких текущих позиций

4. **Сохранение данных**
   - Сохранение/обновление основного профиля
   - Добавление новых записей работы/образования
   - Обновление лимитов API

## Особенности реализации

1. **Денормализация данных**
   - Часто используемые поля вынесены в основную таблицу
   - Упрощает запросы и улучшает производительность
   - Требует поддержания актуальности при обновлениях

2. **Накопительное хранение**
   - Новые записи работы/образования добавляются
   - Старые записи сохраняются для истории
   - Позволяет отслеживать изменения в карьере

3. **Отказоустойчивость**
   - Сохранение сырых данных в отдельной транзакции
   - Логирование всех этапов обработки
   - Обработка ошибок API и сети


## Архитектура сервиса

### 1. Провайдеры данных LinkedIn

**Фабрика парсеров**
- Абстрактный класс `LinkedInParser` с общим интерфейсом
- Реализации для разных провайдеров:
  - `ScrapinParser` - основной парсер через Scrapin API
  - `TomQuirkParser` - для управления аккаунтом (в разработке)
- Фабричный метод создает нужный парсер на основе конфигурации

**Управление провайдерами**
- Автоматический выбор доступного провайдера
- Проверка лимитов перед использованием
- Переключение при исчерпании лимитов
- Обработка специфичных ошибок каждого провайдера

### 2. Слои сервиса

**Repository Layer**
- Абстракция для работы с API LinkedIn
- Обработка ошибок сети
- Управление лимитами запросов

**Service Layer**
- Бизнес-логика обработки профилей
- Валидация данных
- Преобразование форматов
- Подготовка данных для сохранения

**Database Layer**
- ORM модели для работы с БД
- Транзакционное сохранение
- Накопительное хранение истории
- Денормализация данных

### 3. Обработка сообщений

**PubSub Consumer**
- Асинхронная обработка задач
- Управление подпиской
- Обработка ошибок
- Подтверждение выполнения

**Message Handler**
- Валидация входящих сообщений
- Маршрутизация задач
- Формирование ответов
- Отправка уведомлений

### 4. Конфигурация

**Провайдеры**
```python
class LinkedInParserType(str, Enum):
    SCRAPIN = "scrapin"
    TOMQUIRK = "tomquirk"


TODO: при миграции данных последовательности перв. ключей обновить - иначе конфликты при записи новых данных

___
Ручной тест эндпоинтов:

##
1) "Создать задачу в брокере" эндпоинт /tasks/create
Тестирование эндпоинта /tasks/create
curl -X POST "http://localhost:8000/tasks/create" -H "Content-Type: application/json" -d "{\"username\": \"pavellukyanov\", \"target_company_label\": \"Yandex\"}"


curl -X POST "https://linkedin-verifier-331173798018.us-east4.run.app/tasks/create" -H "Content-Type: application/json" -d "{\"username\": \"tmakhalova\", \"target_company_label\": \"Yandex\"}"

##
2) "Получение и обработка задания на парсинг" эндпоинт /pubsub/push
//Для тестирования этого эндпоинта нам нужно создать сообщение в формате PubSub с данными в base64.

Шаг 1: Создание файла с данными задачи
Создайте файл task.json с содержимым:
echo {"username": "pavellukyanov", "target_company_label": "Yandex"} > task.json

Шаг 2: Кодирование данных в base64
В Windows cmd нет прямого эквивалента команды base64, поэтому мы используем PowerShell для кодирования:
powershell -Command "[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Raw task.json)))" > encoded.txt

Шаг 3: Создание файла с сообщением PubSub
Создайте файл pubsub-message.json с шаблоном сообщения:
echo {^
  "message": {^
    "data": "PLACEHOLDER",^
    "message_id": "test-message-id",^
    "publish_time": "2023-01-01T00:00:00.000Z"^
  },^
  "subscription": "projects/your-project-id/subscriptions/linkedin-tasks-sub"^
} > pubsub-message.json

Шаг 4: Замена PLACEHOLDER на закодированные данные
powershell -Command "(Get-Content pubsub-message.json) -replace 'PLACEHOLDER', (Get-Content encoded.txt) | Set-Content pubsub-message.json"

Шаг 5: Отправка запроса
curl -X POST "http://localhost:8000/pubsub/push" -H "Content-Type: application/json" -d @pubsub-message.json
