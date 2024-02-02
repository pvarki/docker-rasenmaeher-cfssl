"""CLI commands for the OCSP rest wrapper"""
import asyncio
import logging

import click
from libadvian.logging import init_logging
from aiohttp import web

from ocsprest import __version__
from ocsprest.config import RESTConfig
from ocsprest.routes import get_app
from ocsprest.helpers import dump_crl, refresh_oscp

LOGGER = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option("-l", "--loglevel", help="Python log level, 10=DEBUG, 20=INFO, 30=WARNING, 40=CRITICAL", default=30)
@click.option("-v", "--verbose", count=True, help="Shorthand for info/debug loglevel (-v/-vv)")
def cligrp(loglevel: int, verbose: int) -> None:
    """REST wrapper for CFSSL CLI functionality not present in it's own REST API"""
    if verbose == 1:
        loglevel = 20
    if verbose >= 2:
        loglevel = 10
    init_logging(loglevel)
    LOGGER.setLevel(loglevel)


@cligrp.command(name="config")
def dump_config() -> None:
    """Show the resolved config as JSON"""
    click.echo(RESTConfig.singleton().model_dump_json())


@cligrp.command(name="crl")
def crl() -> None:
    """Show the resolved config as JSON"""
    asyncio.get_event_loop().run_until_complete(dump_crl())


@cligrp.command(name="serve")
def start_server() -> None:
    """Start the REST API server"""
    cnf = RESTConfig.singleton()
    loop = asyncio.get_event_loop()

    async def refresher() -> None:
        """Dump the CRL and refresh OCSP periodically"""
        try:
            while True:
                await asyncio.gather(dump_crl(), refresh_oscp())
                await asyncio.sleep(cnf.crl_refresh)
        except asyncio.CancelledError:
            LOGGER.debug("Cancelled")

    task = loop.create_task(refresher())
    LOGGER.info("Starting runner on port {}".format(cnf.port))
    web.run_app(get_app(), host=cnf.addr, port=cnf.port, loop=loop)
    task.cancel("run_app returned")


def ocsprest_cli() -> None:
    """cli entrypoint"""
    init_logging(logging.WARNING)
    cligrp()  # pylint: disable=no-value-for-parameter
