## Библиотека для работы с конфигам

### Положения

1.  Библиотека должна минимально расширить функциональность `pydantic_settings`, оставляя всю гибкость этого инструмента
2. Любая настройка должны быть в файле
3. Есть корневой файл с настройками, который может ссылаться на другие файлы. Например, секреты. Ссылки на другие файлы, кроме как из корневого конфига, нежелательны
4. В корневом файле не должно быть ничего секретного (логины, пароли, токены итд)
![enter image description here](https://drive.google.com/thumbnail?id=1OAdkdwUSRp9ZNnct7tOUnB9ntsLeJe-y&sz=w1000)

### Использование
Попробуем описать структуру с картинки. Пусть файловая система организована следующим образом:

```
/home
	/common_config
	/tg_dir
		/tg_token
	/s3
		/s3_credentials.json
	/db
		/db_credentials
```

Код:
```python
# Класс, описывающий файл common_config
class Settings(PlatformSettings): # Наследуемся от классса PlatformSettings
	port: int # 8080 
	setup: str # production
	client_num: int	# 5
	tg_token_path: str # /home/tg_dir/tg_token <- просто файл с какой-то строкой
	s3_cred_path: str # /home/s3/s3_credentials.json <- файл с json-содержимым
	db_cred_path: str # /home/db/db_credentials <- файл формата pydantic_settings со структурой, описанной в PlatformPGSettings
	"""
	class PlatformPGSettings(BaseSettings):  
	    db_host: SecretStr  
	    db_port: int  
		db_name: SecretStr  
	    db_user: SecretStr  
	    db_pass: SecretStr  
	    db_schema: str
	"""
	
    model_config = SettingsConfigDict(  
        env_file=os.environ.get("DOTENV", ".env"), env_file_encoding="utf8"  
    )
```

Теперь нам надо передать в переменную окружения `DOTENV` путь до файла с конфигом:

`export DOTENV=/home/common_config`

Обращение к субконфигам:

```python
# Создаем объект конфига
settings = Settings()


# Читаем pydantic_settings
db_settings = settings.read_dotenv_config('db_config', PlatformPGSettings)
# Создаем фабрику для создания сессий
engine: AsyncEngine = create_async_engine(  
    url=db_settings.database_url_asyncpg.get_secret_value()  
)  
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


# Читаем файл с токеном
try:  
    TOKEN = settings.read_file('tg_token_path')  
except Exception as e:  
    logger.critical(f"Unable to read еп token file {settings.tg_token_path}")  
    raise


# Читаем JSON
try:  
    USER = settings.read_json_file('s3_cred_path')['user']
except Exception as e:  
    logger.critical(f"Unable to read еп token file {settings.s3_cred_path}")  
    raise
```
