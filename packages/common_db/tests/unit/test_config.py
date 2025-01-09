import pytest

import pydantic


@pytest.mark.skip("Temporarily disabled")
def test_import_config_no():
    with pytest.raises(pydantic.ValidationError):
        from common_db.config import settings  # noqa: F401
