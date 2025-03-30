"""pytest automagics"""

from typing import Generator
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from libadvian.logging import init_logging
from libadvian.testhelpers import nice_tmpdir_ses, monkeysession  # pylint: disable=W0611

from ocsprest.routes import get_app

init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


# pylint: disable=W0621
@pytest.fixture(autouse=True, scope="session")
def default_env(monkeysession: pytest.MonkeyPatch, nice_tmpdir_ses: str) -> Generator[None, None, None]:
    """Setup some default environment variables"""
    datadir = Path(nice_tmpdir_ses) / "data"
    cadir = datadir / "ca_public"
    cadir.mkdir(parents=True, exist_ok=True)
    crlfile = cadir / "crl.der"
    with monkeysession.context() as mpatch:
        crlfile.write_text("DUMMY")
        mpatch.setenv("CI", "true")
        mpatch.setenv("OR_DATA_PATH", str(datadir))
        mpatch.setenv("OR_CFSSL", "fakessl")
        mpatch.setenv("OR_CRL", str(crlfile))
        yield None


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Client with app instance"""
    client = TestClient(get_app())
    yield client
