import os

from pydantic import BaseModel

from config_library.field import FieldType


def test_field():
    os.environ['EXAMPLE_VALUE'] = 'example'

    class ExampleEnv(BaseModel):
        example_value: str

    class Example(BaseModel):
        model_config = dict(validate_default=True)

        example: FieldType[ExampleEnv] = 'env'

    example = Example()

    assert example.example.example_value == 'example'
