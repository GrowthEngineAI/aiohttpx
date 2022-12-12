import typing
from lazyops.types import BaseSettings, lazyproperty

class AwsSettings(BaseSettings):
    """
    Settings for AWS
    """
    aws_access_token: typing.Optional[str] = None
    aws_access_key_id: typing.Optional[str] = None
    aws_secret_access_key: typing.Optional[str] = None

    class Config:
        env_prefix = ""


class Settings(BaseSettings):
    """
    Settings for the aiohttpx package
    """
    num_workers: typing.Optional[int] = 4
    soup_enabled: typing.Optional[bool] = False
    debug: typing.Optional[bool] = False

    class Config:
        env_prefix = "AIOHTTPX_"

    @lazyproperty
    def aws(self) -> AwsSettings:
        return AwsSettings()
    

settings = Settings()