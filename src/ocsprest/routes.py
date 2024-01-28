"""aiohttp routes"""
from typing import List
import logging
import tempfile
import uuid
from pathlib import Path
import json

from aiohttp import web

from .config import RESTConfig
from .helpers import call_cmd, cfssl_loglevel, dump_crl, crlpaths

LOGGER = logging.getLogger(__name__)


async def refresh_all(request: web.Request) -> web.Response:
    """calls cfssl ocsprefresh"""
    _ = request
    cnf = RESTConfig.singleton()
    args: List[str] = [
        str(cnf.cfssl),
        "ocsprefresh",
        f"-db-config {cnf.dbconf}",
        f"-ca {cnf.cacrt}",
        f"-ca-key {cnf.cakey}",
        f"-responder {cnf.respcrt}",
        f"-responder-key {cnf.respkey}",
        f"-loglevel {cfssl_loglevel()}",
    ]
    cmd = " ".join(args)
    LOGGER.info("Running ocsprefresh")
    ret, _, _ = await call_cmd(cmd)
    if ret != 0:
        return web.json_response(
            {"success": False, "error": f"CFSSL CLI call to ocsprefresh failed, code {ret}. See server logs"},
            status=500,
        )
    return web.json_response({"success": True})


async def sign_one(request: web.Request) -> web.Response:
    """calls cfssl ocspsign"""
    data = await request.json()
    certtmp = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.pem"
    try:
        certtmp.write_text(data["cert"])
        status = data.get("status", "good")

        cnf = RESTConfig.singleton()
        args: List[str] = [
            str(cnf.cfssl),
            "ocspsign",
            f"-cert {certtmp}",
            f"-ca {cnf.cacrt}",
            f"-status={status}",
            f"-responder {cnf.respcrt}",
            f"-responder-key {cnf.respkey}",
            f"-loglevel {cfssl_loglevel()}",
        ]
        cmd = " ".join(args)
        LOGGER.info("Running ocspsign")
        ret, out, _ = await call_cmd(cmd)
        # TODO: How to inject the response to the database ??
        _resp = json.loads(out)
        if ret != 0:
            return web.json_response(
                {"success": False, "error": f"CFSSL CLI call to ocspsign failed, code {ret}. See server logs"},
                status=500,
            )
        # TODO: Should we return the signed OCSP response ? can rmapi do something with it ??
        return web.json_response({"success": True})
    finally:
        certtmp.unlink()


async def call_dump_crl(request: web.Request) -> web.Response:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    _ = request
    ret = await dump_crl()
    if ret != 0:
        return web.json_response(
            {"success": False, "error": f"CFSSL CLI call to crl failed, code {ret}. See server logs"},
            status=500,
        )
    return web.json_response({"success": True})


async def get_crl_pem(request: web.Request) -> web.Response:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    _ = request
    ret = await dump_crl()
    if ret != 0:
        return web.json_response(
            {"success": False, "error": f"CFSSL CLI call to crl failed, code {ret}. See server logs"},
            status=500,
        )
    _, pem_path = crlpaths()
    return web.Response(body=pem_path.read_bytes(), content_type="application/x-pem-file")


async def get_crl_der(request: web.Request) -> web.Response:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    _ = request
    ret = await dump_crl()
    if ret != 0:
        return web.json_response(
            {"success": False, "error": f"CFSSL CLI call to crl failed, code {ret}. See server logs"},
            status=500,
        )
    der_path, _ = crlpaths()
    return web.Response(body=der_path.read_bytes(), content_type="application/pkix-crl")


def get_app() -> web.Application:
    """Get the app"""
    app = web.Application()
    app.add_routes(
        [
            web.post("/api/v1/refresh", refresh_all),
            web.post("/api/v1/sign", sign_one),
            web.post("/api/v1/dump_crl", call_dump_crl),
            web.post("/api/v1/crl/crl.pem", get_crl_pem),
            web.post("/api/v1/crl/crl.der", get_crl_der),
        ]
    )
    LOGGER.debug("Returning {}".format(app))
    return app
