import pytest


@pytest.fixture
def fs_test_path(request):
    return request.node.path.parent


@pytest.fixture
def fs_test_path_static(fs_test_path, request):
    name = request.node.path.stem.split('.')[0]
    return fs_test_path / 'static' / name

