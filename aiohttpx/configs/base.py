import os
import typing
from aiohttpx.imports.pyd import BaseSettings, validator
from aiohttpx.imports.classprops import lazyproperty


class AwsSettings(BaseSettings):
    """
    Settings for AWS
    """
    aws_access_token: typing.Optional[str] = None
    aws_access_key_id: typing.Optional[str] = None
    aws_secret_access_key: typing.Optional[str] = None

    class Config:
        env_prefix = ""



def is_debug_mode():
    """
    Check Log Levels for Debug Mode
    """
    level = os.getenv("LOGGER_LEVEL", os.getenv("LOG_LEVEL", "INFO"))
    return level == "DEBUG"

class AiohttpxSettings(BaseSettings):
    """
    Settings for the `aiohttpx` package
    """

    num_workers: typing.Optional[int] = 4
    soup_enabled: typing.Optional[bool] = False
    debug: typing.Optional[bool] = None

    class Config:
        env_prefix = "AIOHTTPX_"

    @lazyproperty
    def aws(self) -> AwsSettings:
        """
        Returns the AWS settings
        """
        return AwsSettings()

    @validator("debug", always = True)
    def validate_debug(cls, v: typing.Optional[bool], values: dict) -> bool:
        """
        Validate the debug setting
        """
        if v is None: v = values.get(
            "debug", 
            is_debug_mode()
        )
        if v is False:
            from aiohttpx.utils.logs import mute_httpx_logger
            mute_httpx_logger()
        return v