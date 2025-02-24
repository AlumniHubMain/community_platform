"""
Скрипт для миграции данных LinkedIn профилей между базами данных.
"""
from datetime import datetime
from pathlib import Path
import json
from loguru import logger

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert

from common_db.models.linkedin import ORMLinkedInProfile, ORMEducation, ORMWorkExperience
from common_db.config import db_settings


def export_profiles_data(source_db_url: str, source_schema: str, output_dir: Path) -> None:
    """
    Выгружает данные из исходной БД в JSON файлы.
    
    Args:
        source_db_url: URL исходной базы данных
        source_schema: Схема БД
        output_dir: Директория для сохранения файлов
    """
    engine = create_engine(source_db_url)
    output_dir.mkdir(exist_ok=True)

    # Запросы для выгрузки данных
    queries = {
        'profiles': f"""
            SELECT * FROM {source_schema}.linkedin_profiles
            ORDER BY id
        """,
        'education': f"""
            SELECT * FROM {source_schema}.linkedin_education
            ORDER BY profile_id, id
        """,
        'work_experience': f"""
            SELECT * FROM {source_schema}.linkedin_experience
            ORDER BY profile_id, id
        """
    }

    try:
        with engine.connect() as conn:
            for table_name, query in queries.items():
                logger.info(f"Экспорт данных из таблицы {table_name}")

                # Выполняем запрос
                result = conn.execute(text(query))

                # Конвертируем строки в словари
                rows = []
                for row in result:
                    row_dict = dict(row._mapping)
                    # Конвертируем даты в строки
                    for key, value in row_dict.items():
                        if isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                    rows.append(row_dict)

                # Сохраняем в JSON
                output_file = output_dir / f"{table_name}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(rows, f, ensure_ascii=False, indent=2)

                logger.info(f"Сохранено {len(rows)} записей в {output_file}")

    except Exception as e:
        logger.error(f"Ошибка при экспорте данных: {e}")
        raise


def import_profiles_data(
        target_db_url: str,
        target_schema: str,
        input_dir: Path,
        batch_size: int = 1000
) -> None:
    """
    Импортирует данные из JSON файлов в целевую БД используя bulk insert.
    
    Args:
        target_db_url: URL целевой базы данных
        target_schema: Схема БД
        input_dir: Директория с JSON файлами
        batch_size: Размер пачки для импорта
    """
    engine = create_engine(target_db_url)

    try:
        # Загружаем данные из JSON
        data = {}
        for table in ['profiles', 'education', 'work_experience']:
            file_path = input_dir / f"{table}.json"
            if not file_path.exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data[table] = json.load(f)

        logger.info(f"Загружено записей: profiles={len(data['profiles'])}, "
                    f"education={len(data['education'])}, "
                    f"work_experience={len(data['work_experience'])}")

        # Маппинг таблиц на ORM модели
        models = {
            'profiles': ORMLinkedInProfile,
            'education': ORMEducation,
            'work_experience': ORMWorkExperience
        }

        # Импортируем данные пачками
        with engine.begin() as conn:
            # Устанавливаем схему для текущей сессии
            conn.execute(text(f"SET search_path TO {target_schema}"))

            for table, rows in data.items():
                logger.info(f"Импорт данных в таблицу {table}")
                model = models[table]

                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]

                    # Конвертируем даты из строк обратно в datetime
                    for row in batch:
                        for field in ['created_at', 'updated_at', 'creation_date', 'start_date', 'end_date']:
                            if field in row and row[field]:
                                row[field] = datetime.fromisoformat(row[field])
                        
                        # Приводим skills и languages к нижнему регистру
                        if table == 'profiles':
                            if 'skills' in row and row['skills']:
                                row['skills'] = [skill.casefold() for skill in row['skills'] if skill]
                            if 'languages' in row and row['languages']:
                                row['languages'] = [lang.casefold() for lang in row['languages'] if lang]

                    # Создаем bulk insert запрос
                    stmt = insert(model).values(batch)

                    # Для profiles обновляем существующие записи, для остальных игнорируем дубликаты
                    if table == 'profiles':
                        stmt = stmt.on_conflict_do_update(
                            index_elements=['id'],
                            set_=dict(updated_at=stmt.excluded.updated_at)  # Обновляем только updated_at
                        )
                    else:
                        stmt = stmt.on_conflict_do_nothing(index_elements=['id'])

                    # Выполняем bulk insert
                    conn.execute(stmt)

                    logger.info(f"Импортировано {i + len(batch)} из {len(rows)} записей")

                logger.info(f"Завершен импорт в таблицу {table}")

        logger.info("Миграция данных завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка при импорте данных: {e}")
        raise


if __name__ == "__main__":
    # Директория для данных
    DATA_DIR = Path(__file__).parent / "data" / "linkedin_profiles_dump"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Параметры БД
    ##
    # Нужно только при выгрузке актуальных (из Я.Облака.Postgres)
    # SOURCE_SCHEMA = "__test_to_del_alh_community_platform"
    # SOURCE_DB_PARAMS = {
    #     "host": "",
    #     "port": 6432,
    #     "dbname": "",
    #     "user": "",
    #     "password": ""
    # }
    # SOURCE_DB_URL = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(**SOURCE_DB_PARAMS)
    #

    #  Куда заливаем - берем db.json из проекта - где креды для Postgres текущей платформы
    TARGET_SCHEMA = db_settings.db.db_schema
    # Заменяем asyncpg на обычный postgresql драйвер
    TARGET_DB_URL = (db_settings.db.database_url_asyncpg
                     .get_secret_value()
                     .replace('postgresql+asyncpg://', 'postgresql://'))

    # Выгрузка данных из БД в файлы (перезапишет соответсвующие json-файлы)
    # export_profiles_data(SOURCE_DB_URL, SOURCE_SCHEMA, DATA_DIR)

    # Зальет исторические данные из json-файлов в указанную БД, схему
    import_profiles_data(TARGET_DB_URL, TARGET_SCHEMA, DATA_DIR)
