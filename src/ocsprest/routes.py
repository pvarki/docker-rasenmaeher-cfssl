"""aiohttp routes"""
from typing import List, Dict, Any
import asyncio
import logging
import tempfile
import uuid
from pathlib import Path
import json

from libadvian.logging import init_logging
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import FileResponse

from ocsprest import __version__
from .config import RESTConfig
from .helpers import call_cmd, cfssl_loglevel, dump_crl, crlpaths, refresh_oscp

LOGGER = logging.getLogger(__name__)
ROUTER = APIRouter()


# FIXME: Use proper response schemas etc


@ROUTER.post("/refresh")
async def refresh_all(request: Request) -> Dict[str, Any]:
    """calls cfssl ocsprefresh"""
    _ = request
    ret = await refresh_oscp()
    if ret != 0:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"CFSSL CLI call to ocsprefresh failed, code {ret}. See server logs"},
        )
    return {"success": True}


@ROUTER.post("/sign")
async def sign_one(request: Request) -> Dict[str, Any]:
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
            raise HTTPException(
                status_code=500,
                detail={"success": False, "error": f"CFSSL CLI call to ocspsign failed, code {ret}. See server logs"},
            )
        # TODO: Should we return the signed OCSP response ? can rmapi do something with it ??
        return {"success": True}
    finally:
        certtmp.unlink()


@ROUTER.post("/dump_crl")
async def call_dump_crl(request: Request) -> Dict[str, Any]:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    _ = request
    ret = await dump_crl()
    if ret != 0:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"CFSSL CLI call to crl failed, code {ret}. See server logs"},
        )
    return {"success": True}


@ROUTER.get("/crl/crl.pem")
async def get_crl_pem(request: Request) -> FileResponse:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    _ = request
    ret = await dump_crl()
    if ret != 0:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"CFSSL CLI call to dump_crl failed, code {ret}. See server logs"},
        )
    _, pem_path = crlpaths()
    return FileResponse(pem_path, media_type="application/x-pem-file")


@ROUTER.get("/crl/crl.der")
async def get_crl_der(request: Request) -> FileResponse:
    """Dump CRL to shared directory, triggering reloads for everyone interested in it is beyond us though"""
    _ = request
    ret = await dump_crl()
    if ret != 0:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": f"CFSSL CLI call to dump_crl failed, code {ret}. See server logs"},
        )
    der_path, _ = crlpaths()
    return FileResponse(der_path, media_type="application/pkix-crl")


@ROUTER.get("/healthcheck")
async def healthcheck(request: Request) -> Dict[str, Any]:
    """Health check"""
    _ = request
    # TODO: should be actually test something ?
    return {"healthcheck": "success"}


def get_app() -> FastAPI:
    """Get the app"""
    app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json", version=__version__)
    app.include_router(router=ROUTER, prefix="/api/v1")
    LOGGER.debug("Returning {}".format(app))
    return app


def app_w_logging() -> FastAPI:
    """init logging and create app"""
    init_logging()
    app = get_app()
    return app


async def refresher() -> None:
    """Dump the CRL and refresh OCSP periodically"""
    try:
        while True:
            await asyncio.gather(dump_crl(), refresh_oscp())
            await asyncio.sleep(RESTConfig.singleton().crl_refresh)
    except asyncio.CancelledError:
        LOGGER.debug("Cancelled")
