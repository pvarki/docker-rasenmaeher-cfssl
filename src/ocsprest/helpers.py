"""helpers"""
from typing import Tuple, List
import logging
import asyncio
import base64

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from .config import RESTConfig

LOGGER = logging.getLogger(__name__)


async def call_cmd(cmd: str, timeout: int = 10) -> Tuple[int, str, str]:
    """Do the boilerplate for calling cmd and reporting output/return code"""
    cnf = RESTConfig.singleton()
    cwd_cmd = f"cd {cnf.data_path} && {cmd}"
    LOGGER.debug("Calling create_subprocess_shell(({})".format(cwd_cmd))
    process = await asyncio.create_subprocess_shell(
        cwd_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await asyncio.wait_for(process.communicate(), timeout=timeout)
    if err:
        LOGGER.warning(err)
    LOGGER.info(out)
    assert isinstance(process.returncode, int)  # at this point it is, keep mypy happy
    if process.returncode != 0:
        LOGGER.error("{} returned nonzero code: {} (process: {})".format(cmd, process.returncode, process))
        LOGGER.error(err)
        LOGGER.error(out)

    return process.returncode, out.decode("utf-8"), err.decode("utf-8")


def cfssl_loglevel() -> int:
    """Return CFSSL loglevel 0-5"""
    our_level = LOGGER.getEffectiveLevel()
    if our_level < 10:
        return 0
    return round(our_level / 10) - 1


async def dump_crl() -> int:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    cnf = RESTConfig.singleton()
    args: List[str] = [
        str(cnf.cfssl),
        "crl",
        f"-db-config {cnf.dbconf}",
        f"-ca {cnf.cacrt}",
        f"-ca-key {cnf.cakey}",
        f"-expiry {cnf.crl_lifetime}",
        f"-loglevel {cfssl_loglevel()}",
    ]
    cmd = " ".join(args)
    ret, der_b64, _ = await call_cmd(cmd)
    if ret != 0:
        return ret
    der_bytes = base64.b64decode(der_b64)
    LOGGER.info("Writing {}".format(cnf.crl))
    cnf.crl.write_bytes(der_bytes)
    LOGGER.debug("Parsing the CRL")
    crl = x509.load_der_x509_crl(der_bytes)
    pem_path = cnf.crl.parent / f"{cnf.crl.stem}.pem"
    LOGGER.info("Writing {}".format(pem_path))
    pem_path.write_bytes(crl.public_bytes(encoding=serialization.Encoding.PEM))
    return ret
