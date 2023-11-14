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
    cfssl_path: Path = Field(description="cfssl executable path", default="/usr/bin/cfssl")
    data_path: Path = Field(
        description="Where is CFSSL persistent data", alias="CFSSL_PERSISTENT_FOLDER", default="/data/persistent"
    )

    ci: bool = Field(default=False, alias="CI", description="Are we running in CI")
    model_config = SettingsConfigDict(env_prefix="or_", env_file=".env", extra="ignore", env_nested_delimiter="__")
    _singleton: ClassVar[Optional[RESTConfig]] = None

    @classmethod
    def singleton(cls) -> RESTConfig:
        """Return singleton"""
        if not RESTConfig._singleton:
            RESTConfig._singleton = RESTConfig()
        return RESTConfig._singleton
