import os

from pydantic import BaseModel

from config_library.storage import Storage


def test_storage():
    class Example(BaseModel):
        example_value: str

    storage = Storage()

    storage.register('env', Example)

    os.environ['EXAMPLE_VALUE'] = 'example'

    value = storage.get('env', Example)
    assert value.example_value == 'example'
