"""helpers"""
from typing import Tuple
import logging
import asyncio

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
