from config_library import ReloadableFieldType, BaseConfig


def test_reload_field(tmp_path):
    with open(tmp_path / 'token', 'w') as f:
        f.write('ABCD:THIS_IS_TOKEN')

    class Conf(BaseConfig):
        example: ReloadableFieldType[str] = f'{str(tmp_path)}/token'

    conf = Conf()
    assert conf.example.value == 'ABCD:THIS_IS_TOKEN'

    with open(tmp_path / 'token', 'w') as f:
        f.write('ABCD:NEW_TOKEN')

    conf.example.reload()
    assert conf.example.value == 'ABCD:NEW_TOKEN'