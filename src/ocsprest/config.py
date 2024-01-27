"""Config"""
from __future__ import annotations
from typing import ClassVar, Optional
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RESTConfig(BaseSettings):
    """Config for for the wrapper REST api"""

    port: int = Field(description="bind port", default=8887)
    addr: str = Field(description="bind address", default="0.0.0.0")  # nosec
    cfssl: Path = Field(description="cfssl executable path", default="/usr/bin/cfssl")
    data_path: Path = Field(
        description="Where is CFSSL persistent data", alias="CFSSL_PERSISTENT_FOLDER", default="/data/persistent"
    )
    cacrt: Path = Field(
        alias="RUN_INTER_CA", description="CA cert to use in commands", default="/data/persistent/inter-ca.pem"
    )
    cakey: Path = Field(
        alias="RUN_INTER_CA_KEY", description="CA key to use in commands", default="/data/persistent/inter-ca_key.pem"
    )
    rootcacrt: Path = Field(
        alias="RUN_CA", description="Root CA cert to use in commands", default="/data/persistent/ca.pem"
    )
    rootcakey: Path = Field(
        alias="RUN_CA_KEY", description="root CA key to use in commands", default="/data/persistent/init_ca-key.pem"
    )
    dbconf: Path = Field(
        alias="RUN_DB_CONFIG", description="Path to the db config file", default="/data/persistent/db.json"
    )
    respcrt: Path = Field(
        alias="RUN_OCSP_CERT", description="Responder cert to use", default="/data/persistent/ocsp.pem"
    )
    respkey: Path = Field(
        alias="RUN_OCSP_KEY", description="Responder key to use", default="/data/persistent/ocsp_key.pem"
    )
    crl: Path = Field(
        description="Location to dump the DER CRL to, .PEM version will also be created", default="/ca_public/crl.der"
    )
    crl_lifetime: str = Field(description="Lifetime to pass to CFSSL", default="1800s")
    crl_refresh: int = Field(description="Interval to dump CRL via out background task", default=900)

    ci: bool = Field(default=False, alias="CI", description="Are we running in CI")
    model_config = SettingsConfigDict(env_prefix="or_", env_file=".env", extra="ignore", env_nested_delimiter="__")
    _singleton: ClassVar[Optional[RESTConfig]] = None

    @classmethod
    def singleton(cls) -> RESTConfig:
        """Return singleton"""
        if not RESTConfig._singleton:
            RESTConfig._singleton = RESTConfig()
        return RESTConfig._singleton
