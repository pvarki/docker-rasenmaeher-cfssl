"""aiohttp routes"""
from typing import List
import logging

from aiohttp import web

from .config import RESTConfig
from .helpers import call_cmd, cfssl_loglevel

LOGGER = logging.getLogger(__name__)


async def refresh_all(request: web.Request) -> web.Response:
    """calls cfssl ocsprefresh as a background task"""
    _ = request
    cnf = RESTConfig.singleton()
    args: List[str] = [
        str(cnf.cfssl),
        f"-ca {cnf.cacrt}",
        f"-ca-key {cnf.cakey}",
        f"-responder {cnf.respcrt}",
        f"-responder-key {cnf.respkey}",
        f"-loglevel {cfssl_loglevel()}",
    ]
    cmd = " ".join(args)
    LOGGER.info("Running ocsprefresh")
    ret = await call_cmd(cmd)
    if ret != 0:
        return web.json_response(
            {"success": False, "error": f"CFSSL CLI call to ocsprefresh failed, code {ret}. See server logs"},
            status=500,
        )
    return web.json_response({"success": True})


def get_app() -> web.Application:
    """Get the app"""
    app = web.Application()
    app.add_routes(
        [
            web.post("/api/v1/refresh", refresh_all),
        ]
    )
    LOGGER.debug("Returning {}".format(app))
    return app
