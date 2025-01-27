# LinkedIn Verification Service

## Общее описание
Сервис предназначен для верификации профилей LinkedIn, с фокусом на опыт работы в целевой компании. 
Реализована денормализация данных для оптимизации частых запросов.

## Основные компоненты

### 1. Обработка текущей работы
- Определяется наличие текущей работы (записи без end_date)
- Подсчитывается количество текущих мест работы
- Сохраняется информация о последней активной работе:
  - Название компании
  - LinkedIn ID компании
  - Должность
  - URL компании

### 2. Обработка целевой компании
- Поиск всех позиций в целевой компании (case-insensitive поиск по названию)
- Подсчет количества позиций в целевой компании
- Определение последней позиции:
  - Сортировка по дате начала (от новых к старым)
  - Использование безопасной даты (1900-01-01) для записей без даты
  - Сохранение информации о последней позиции
- Проверка текущей работы в целевой компании

### 3. Денормализация данных
Для оптимизации запросов следующие поля вынесены в основную таблицу профиля:

#### Текущая работа:
```python
is_currently_employed: bool       # Есть ли текущая работа
current_jobs_count: int          # Количество текущих работ
current_company_label: str       # Название текущей компании
current_company_linkedin_id: str # LinkedIn ID компании
current_position_title: str      # Должность
current_company_linkedin_url: str # URL компании
```

#### Целевая компания:
```python
is_target_company_found: bool    # Найдена ли целевая компания
target_company_positions_count: int # Количество позиций
target_company_label: str        # Название компании
target_company_linkedin_id: str  # LinkedIn ID
target_position_title: str       # Последняя должность
target_company_linkedin_url: str # URL компании
is_employee_in_target_company: bool # Работает ли сейчас
```

## Процесс верификации

1. **Получение данных**:
   ```python
   raw_data = await repository.get_profile(username)
   profile = LinkedInProfileResponse.model_validate(raw_data)
   ```

2. **Обработка текущей работы** (в extract_nested_fields):
   ```python
   current_jobs = [pos for pos in positions if not pos.end_date]
   current_job = current_jobs[0] if current_jobs else None
   ```

3. **Проверка целевой компании** (в validate_work_experience):
   ```python
   target_positions = [
       exp for exp in profile.work_experience
       if target_company_label.lower() in (exp.company_label or '').lower()
   ]
   ```

4. **Сохранение результатов**:
   - Все изменения сохраняются в рамках одной транзакции
   - При ошибках устанавливаются значения по умолчанию
   - Обновляется статус верификации в основном профиле

## Особенности реализации

1. **Безопасная обработка данных**:
   - Проверки на None
   - Безопасное приведение строк к нижнему регистру
   - Обработка отсутствующих дат

2. **Оптимизация производительности**:
   - Денормализация часто используемых данных
   - Индексы для основных полей поиска
   - Минимизация обращений к связанным таблицам

3. **Консистентность данных**:
   - Атомарные транзакции
   - Валидация данных через Pydantic
   - Согласованность между ORM и Pydantic моделями

## TODO
- Возможно вынести денормализованные поля в головную таблицу User
- Добавить кэширование часто запрашиваемых данных
- Реализовать периодическое обновление статусов

## Примечания
- Все булевы поля имеют префикс `is_` для единообразия
- Поля с датами используют первый день месяца, так как API предоставляет только месяц и год
- Сохраняются raw данные для возможного дебага/аудита 

## Database Setup

### Schema Creation and Permissions

Before running migrations, you need to set up the database schema and permissions. Execute the following SQL script as a database administrator:

```sql
-- Выполнять от имени YNDXFamily_db_owner (владелец БД в Яндекс.Облаке)

-- Создаем схему от имени владельца БД
CREATE SCHEMA IF NOT EXISTS linkedin_test;

-- Создаем сервисного пользователя, если еще не создан
-- DO $$ 
-- BEGIN
--   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'platform_companies_service') THEN
--     CREATE USER platform_companies_service WITH PASSWORD 'your_password';
--   END IF;
-- END
-- $$;

-- Даем права на создание объектов в схеме сервисному аккаунту
GRANT CREATE, USAGE ON SCHEMA linkedin_test TO platform_companies_service;

-- Даем права на использование схемы
GRANT USAGE ON SCHEMA linkedin_test TO platform_companies_service;

-- Права на все существующие таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA linkedin_test TO platform_companies_service;

-- Права на будущие таблицы
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test 
GRANT ALL PRIVILEGES ON TABLES TO platform_companies_service;

-- Права на существующие последовательности
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA linkedin_test TO platform_companies_service;

-- Права на будущие последовательности
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test
GRANT ALL PRIVILEGES ON SEQUENCES TO platform_companies_service;

-- Права на функции (существующие и будущие)
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA linkedin_test TO platform_companies_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test
GRANT ALL PRIVILEGES ON FUNCTIONS TO platform_companies_service;

-- Права на процедуры (существующие и будущие)
GRANT ALL PRIVILEGES ON ALL PROCEDURES IN SCHEMA linkedin_test TO platform_companies_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test
GRANT ALL PRIVILEGES ON PROCEDURES TO platform_companies_service;

-- Дополнительные права для миграций
-- Права на изменение структуры таблиц
GRANT ALL ON ALL TABLES IN SCHEMA linkedin_test TO platform_companies_service WITH GRANT OPTION;
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test 
GRANT ALL ON TABLES TO platform_companies_service WITH GRANT OPTION;

-- Права на типы данных
GRANT ALL ON ALL TYPES IN SCHEMA linkedin_test TO platform_companies_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test 
GRANT ALL ON TYPES TO platform_companies_service;

-- Права на создание/изменение индексов
GRANT ALL ON ALL INDEXES IN SCHEMA linkedin_test TO platform_companies_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test 
GRANT ALL ON INDEXES TO platform_companies_service;

-- Права на создание/изменение ограничений
GRANT ALL ON ALL SEQUENCES IN SCHEMA linkedin_test TO platform_companies_service WITH GRANT OPTION;
ALTER DEFAULT PRIVILEGES IN SCHEMA linkedin_test 
GRANT ALL ON SEQUENCES TO platform_companies_service WITH GRANT OPTION;
```

### Что делает этот скрипт:

1. Создает схему `linkedin_test` от имени владельца БД (YNDXFamily_db_owner)
2. Дает все необходимые права сервисному аккаунту:
   - Права на создание объектов в схеме (CREATE)
   - Права на использование схемы (USAGE)
   - Права на все существующие и будущие таблицы
   - Права на последовательности
   - Права на функции и процедуры
3. Дает дополнительные права для миграций:
   - WITH GRANT OPTION для передачи прав
   - Права на типы данных
   - Права на индексы
   - Права на ограничения и последовательности

### Важные моменты:

1. Скрипт выполняется от имени YNDXFamily_db_owner (владелец БД в Яндекс.Облаке)
2. Сервисный аккаунт получает права на создание и управление объектами
3. Владелец БД сохраняет все права на схему
4. Закомментирован блок создания пользователя, так как в Яндекс.Облаке это делается через UI

### Проверка прав:

После выполнения скрипта можно проверить права:

```sql
-- Проверка существования схемы
SELECT schema_name, schema_owner 
FROM information_schema.schemata 
WHERE schema_name = 'linkedin_test';

-- Проверка прав на схему
SELECT has_schema_privilege('platform_companies_service', 'linkedin_test', 'CREATE');
SELECT has_schema_privilege('platform_companies_service', 'linkedin_test', 'USAGE');

-- Проверка прав на таблицы
SELECT has_table_privilege('platform_companies_service', 'linkedin_test.table_name', 'ALL');
```

### Следующие шаги:

1. Убедитесь, что скрипт выполнен успешно
2. Проверьте права сервисного аккаунта
3. Настройте подключение к БД в конфигурации сервиса
4. Запустите миграции через Alembic

### Безопасность:

- Храните параметры подключения к БД в защищенном месте
- Используйте разные схемы для разных окружений (dev, test, prod)
- Регулярно проверяйте и обновляйте права доступа
- Следите за безопасностью паролей пользователей БД 