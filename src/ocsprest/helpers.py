"""helpers"""
import logging
import asyncio

LOGGER = logging.getLogger(__name__)


async def call_cmd(cmd: str, timeout: int = 10) -> int:
    """Do the boilerplate for calling cmd and reporting output/return code"""
    LOGGER.debug("Calling create_subprocess_shell(({})".format(cmd))
    process = await asyncio.create_subprocess_shell(
        cmd,
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

    return process.returncode


def cfssl_loglevel() -> int:
    """Return CFSSL loglevel 0-5"""
    our_level = LOGGER.getEffectiveLevel()
    if our_level < 10:
        return 0
    return round(our_level / 10) - 1
