from config_library import FieldType, BaseConfig


def test_raw_str_field(fs_test_path_static):
    class Conf(BaseConfig):
        example: FieldType[str] = f'{str(fs_test_path_static)}/token'

    conf = Conf()
    assert conf.example == 'ABCD:THIS_IS_TOKEN'


def test_raw_int_field(fs_test_path_static):
    class Conf(BaseConfig):
        example: FieldType[int] = f'{str(fs_test_path_static)}/number'

    conf = Conf()
    assert conf.example == 123456


def test_raw_float_field(fs_test_path_static):
    class Conf(BaseConfig):
        example: FieldType[float] = f'{str(fs_test_path_static)}/float'

    conf = Conf()
    assert conf.example == 123.456
