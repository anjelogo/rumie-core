import os

import pytest

INTEGRATION_ENABLED = os.getenv("RUN_INTEGRATION") == "1"

integration = pytest.mark.skipif(
    not INTEGRATION_ENABLED,
    reason="requires mongo replica set; set RUN_INTEGRATION=1 with docker compose up",
)
