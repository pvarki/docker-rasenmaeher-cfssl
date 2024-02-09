"""CLI commands for the OCSP rest wrapper"""
import asyncio
import logging
import json

import click
from libadvian.logging import init_logging
from aiohttp import web
import aiohttp

from ocsprest import __version__
from ocsprest.config import RESTConfig
from ocsprest.routes import get_app, refresher
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
    """dump CRL files"""
    asyncio.get_event_loop().run_until_complete(dump_crl())


@cligrp.command(name="ocsp")
def ocsp() -> None:
    """Refresh OCSP signatures"""
    asyncio.get_event_loop().run_until_complete(refresh_oscp())


@cligrp.command(name="serve")
def start_server() -> None:
    """Start the REST API server"""
    cnf = RESTConfig.singleton()
    loop = asyncio.get_event_loop()
    task = loop.create_task(refresher())
    LOGGER.info("Starting runner on port {}".format(cnf.port))
    web.run_app(get_app(), host=cnf.addr, port=cnf.port, loop=loop)
    task.cancel("run_app returned")


@cligrp.command(name="healthcheck")
@click.option("--host", default="localhost", help="The host to connect to")
@click.option("--port", default=8887, help="The port to connect to")
@click.option("--timeout", default=2.0, help="The timeout in seconds")
@click.pass_context
def do_http_healthcheck(ctx: click.Context, host: str, port: int, timeout: float) -> None:
    """
    Do a GET request to the healthcheck api and dump results to stdout
    """

    async def doit() -> int:
        """The actual work"""
        nonlocal host, port, timeout
        if "://" not in host:
            host = f"http://{host}"
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(f"{host}:{port}/api/v1/healthcheck") as resp:
                if resp.status != 200:
                    return resp.status
                payload = await resp.json()
                click.echo(json.dumps(payload))
                if payload["healthcheck"] != "success":
                    return 1
        return 0

    ctx.exit(ctx.obj["loop"].run_until_complete(doit()))


def ocsprest_cli() -> None:
    """cli entrypoint"""
    init_logging(logging.WARNING)
    cligrp()  # pylint: disable=no-value-for-parameter
