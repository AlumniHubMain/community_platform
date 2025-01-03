import os

from pydantic import BaseModel

from config_library.field import FieldType

class ExampleValue(BaseModel):
    example_value: str


def test_field():
    os.environ['EXAMPLE_VALUE'] = 'example'

    class Example(BaseModel):
        model_config = dict(validate_default=True)

        example: FieldType[ExampleValue] = 'env'

    example = Example()

    assert example.example.example_value == 'example'


def test_field_dotenv(fs_test_path_static):
    class ExampleDotEnv(BaseModel):
        example_value: str

    class Example(BaseModel):
        model_config = dict(validate_default=True)

        example: FieldType[ExampleValue] = f'{str(fs_test_path_static)}/example.env'

    example = Example()

    assert example.example.example_value == 'example'


def test_field_json(fs_test_path_static):
    class Example(BaseModel):
        model_config = dict(validate_default=True)

        example: FieldType[ExampleValue] = f'{str(fs_test_path_static)}/example.json'

    example = Example()

    assert example.example.example_value == 'example'


def test_field_yaml(fs_test_path_static):
    class Example(BaseModel):
        model_config = dict(validate_default=True)

        example: FieldType[ExampleValue] = f'{str(fs_test_path_static)}/example.yaml'

    example = Example()

    assert example.example.example_value == 'example'