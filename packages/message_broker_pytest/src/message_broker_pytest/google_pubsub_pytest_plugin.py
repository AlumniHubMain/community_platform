import subprocess

import pytest

from message_broker_pytest.google_pubsub_conf import Config


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini(
        "google_pubsub_project",
        "Google Cloud project ID",
        default="test-project",
    )
    parser.addini(
        "google_pubsub_host_port",
        "Google Cloud Pub/Sub emulator host and port",
        default="localhost:8085",
    )



@pytest.fixture
def google_pubsub_config(request):
    return Config(
        project=request.config.getini("google_pubsub_project"),
        host_port=request.config.getini("google_pubsub_host_port")
    )


@pytest.fixture
def google_pubsub_emulator(google_pubsub_config) -> None:
    start = [
        "gcloud",
        "beta",
        "emulators",
        "pubsub",
        "start",
        f"--project={google_pubsub_config.project}",
        f"--host-port={google_pubsub_config.host_port}",
    ]
    subprocess.Popen(start, stdout=subprocess.PIPE)

    yield

    exec_ps = subprocess.Popen(["ps", "-ef"], stdout=subprocess.PIPE)
    exec_pgrep = subprocess.Popen(
        ["pgrep", "-f", "cloud-pubsub-emulator"], stdin=exec_ps.stdout, stdout=subprocess.PIPE
    )
    subprocess.Popen(["xargs", "kill"], stdin=exec_pgrep.stdout, stdout=subprocess.PIPE)

