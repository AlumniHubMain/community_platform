## Библиотека для работы с конфигам

### Положения

1. Конфиги должны быть деклариративными и по максимуму использовать возможность pydantic
2. Любые настройки для приложений должны быть в файле
3. Есть корневой объект для настроек, который может ссылаться на другие файлы. Например, секреты.
4. В корневом файле не должно быть ничего секретного (логины, пароли, токены итд)

### Использование
Для каждого приложения следует создать свой корневой класс настроек
В этом классе мы прописываем всю схему настроек, которые будет использовать приложение
Поля могут быть указанны как путь до загрузки из
1. ENV
2. Фаил Dotenv
3. Фаил Json
4. Фаил Yaml
5. Raw Фаил (например, для токеннов)

#### Пример:
```python
from pydantic import BaseModel

from config_library import BaseConfig, FieldType

class Db(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db_name: str

class Settings(BaseConfig):
    environment: FieldType[str] = '/configs/environment'
    db: FieldType[Db] = '/configs/db/connect.json'
```

В таком случае мы загрузим значение при создание класса из файлов указынных в полях

```
/configs/
  /environment
  /db
    /connect.json
```

Создание объекта приведет к загрузке из Storage таким образом  
если мы создадим два конфига или два поля которые будут ссылаться на один и тот же фаил и с оди
наковым типом(схемой) конфига то будет загружен только один раз

```python
# Создаем объект конфига
settings = Settings()

```

### Можно доабвить поле которое можно перегружать при не обходимости
```python
from pydantic import BaseModel

from config_library import BaseConfig, FieldType, ReloadableFieldType



class Other(BaseModel):
    change: str

class Settings(BaseConfig):
    environment: FieldType[str] = '/configs/environment'
    other: ReloadableFieldType[Other] = '/configs/other.json'

s = Settings()

# Для доступа к полю вызов по attribute
other = s.other.value

#Для перегрузки поля 
s.other.reload()

```