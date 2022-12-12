import time
import asyncio
import random
import uuid
import typing
import concurrent.futures

from lazyops.utils import logger
from lazyops.types import BaseModel, validator, lazyproperty

from aiohttpx.configs import settings
from aiohttpx.imports.boto import (
    ClientError,
    EndpointConnectionError,
    BotoSession,
    AsyncBotoClient,
    AsyncBotoSession,
    require_boto,
)

_aws_regions_default = [
    'us-east-1'
]
_aws_regions_us = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
_aws_regions_eu = ["eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1"]
_aws_regions_asia = ["ap-south-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "sa-east-1"]
_aws_regions_all = _aws_regions_us + _aws_regions_eu + _aws_regions_asia

_aws_region_map = {
    'default': _aws_regions_default,
    'us': _aws_regions_us,
    'eu': _aws_regions_eu,
    'asia': _aws_regions_asia,
    'all': _aws_regions_all,
}


__all__ = [
    'ProxyManager',
    'ProxyRegion',
    'ProxyEndpoint',
]

class ProxyEndpoint(BaseModel):
    name: str
    api_id: str
    region: str

    @property
    def endpoint(self):
        return f"{self.api_id}.execute-api.{self.region}.amazonaws.com"
    

class ProxyRegion(BaseModel):
    name: str
    region: str
    num_gateways: typing.Optional[int] = 1
    endpoints: typing.Optional[typing.List[ProxyEndpoint]] = []

    @property
    def num_to_create(self):
        return max(0, self.num_gateways - len(self.endpoints))
    
    @property
    def endpoint_ids(self):
        return [e.api_id for e in self.endpoints]
    
    @property
    def endpoint_urls(self):
        return [e.endpoint for e in self.endpoints]
    
    def filter_endpoints(self, data: typing.List[typing.Dict]):
        """
        Filters from the data the endpoints that match this region
        """
        for api in data:
            if api['name'].startswith(self.name) and api['id'] not in self.endpoint_ids:
                self.endpoints.append(ProxyEndpoint(
                    name = api['name'],
                    api_id= api['id'],
                    region= self.region,
                ))



class ProxyManager(BaseModel):
    """
    Manages the creation and deletion of proxy gateways
    """
    base_url: str
    regions: typing.Optional[typing.Union[str, typing.List[str]]] = 'default'

    gateways_per_region: typing.Optional[int] = 1
    reuse_gateways: typing.Optional[bool] = False
    unique_names: typing.Optional[bool] = False

    regions_data: typing.Optional[typing.Dict[str, ProxyRegion]] = {}

    aws_access_key_id: str = settings.aws.aws_access_key_id
    aws_secret_access_key: str = settings.aws.aws_secret_access_key

    pagination_limit: typing.Optional[int] = 50

    @validator('regions', pre = True, always = True)
    def validate_regions(cls, v):
        if isinstance(v, str):
            # logger.info(f"Using region {v} for proxy gateway")
            return _aws_region_map.get(v, _aws_regions_default)
        return v

    @property
    def base_name(self):
        return f"aiohttpx Proxy Gateway for {self.base_url}"


    @lazyproperty
    def uri(self):
        return self.base_url[:-1] if self.base_url.endswith("/") else self.base_url

    def get_unique_name(self):
        return f"{self.base_name} ({str(uuid.uuid4())})"

    def get_name(self):
        return self.get_unique_name() if self.unique_names else self.base_name
    
    @property
    def all_endpoints(self):
        return [e.endpoint for r in self.regions_data.values() for e in r.endpoints]
    
    @property
    def is_active(self):
        return bool(self.all_endpoints)
    
    def get_region_endpoints(self, region: str):
        return self.regions_data[region].endpoint_urls
    
    def get_randomized_endpoint(self, region: str = None) -> str:
        return random.choice(self.get_region_endpoints(region)) if region \
            else random.choice(self.all_endpoints)

    @require_boto(is_async = False, required = True)
    def build_endpoints(
        self,
    ):
        # resolve_boto(is_async = False, required = True)
        if not self.regions_data:
            self.regions_data = {
                region: ProxyRegion(
                    name = self.base_name,
                    num_gateways = self.gateways_per_region,
                    region = region,
                ) for region in self.regions
            }
            # logger.info(f'Regions: {self.regions_data}')
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.num_workers) as executor:
            for region in self.regions_data:
                if not self.regions_data[region].endpoints:
                    self.regions_data[region].filter_endpoints(
                        self.get_apis(region)
                    )
                if self.regions_data[region].endpoints:
                    logger.info(f"Reusing ({len(self.regions_data[region].endpoints)}) endpoints in {region} for {self.base_url}")
                if self.regions_data[region].num_to_create > 0:
                    logger.info(f"[Sync] Building ({self.regions_data[region].num_to_create}) endpoints in {region} for {self.base_url}")
                    futures = [
                        executor.submit(self.create_api, region) for _ in range(self.regions_data[region].num_to_create)
                    ]
                    _ = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    @require_boto(is_async = True, required = True)
    async def async_build_endpoints(
        self,
    ):
        # _ensure_deps(is_async=True)
        # resolve_boto(is_async = True, required = True)
        if not self.regions_data:
            self.regions_data = {
                region: ProxyRegion(
                    name = self.base_name,
                    num_gateways = self.gateways_per_region,
                    region = region,
                ) for region in self.regions
            }
            # logger.info(f'Regions: {self.regions_data}')
        for region in self.regions_data:
            if not self.regions_data[region].endpoints:
                self.regions_data[region].filter_endpoints(
                    await self.async_get_apis(region)
                )
            if self.regions_data[region].endpoints:
                logger.info(f"Reusing ({len(self.regions_data[region].endpoints)}) endpoints in {region} for {self.base_url}")
            if self.regions_data[region].num_to_create > 0:
                logger.info(f"[Async] Building ({self.regions_data[region].num_to_create}) endpoints in {region} for {self.base_url}")
                await asyncio.gather(*[asyncio.create_task(self.async_create_api(region)) for _ in range(self.regions_data[region].num_to_create)])
                
    

    """
    Client Methods
    """

    def get_aws_client(self, region: str):
        session = BotoSession()
        return session.client(
            "apigateway",
            region_name = region, aws_access_key_id = self.aws_access_key_id, aws_secret_access_key = self.aws_secret_access_key
        )

    """
    Retrieve Endpoints
    """

    def get_apis(
        self, 
        region: str, 
    ) -> typing.List[typing.Dict]:
        position = None
        complete = False
        apis = []
        client = self.get_aws_client(region)
        while not complete:
            try:
                gateways = client.get_rest_apis(limit=self.pagination_limit) \
                        if position is None \
                        else client.get_rest_apis(limit=self.pagination_limit, position=position)
            except (ClientError, EndpointConnectionError):
                logger.error(f"Could not get list of APIs in region \"{region}\"")
                return []
            apis.extend(gateways["items"])
            position = gateways.get("position", None)
            if position is None: complete = True
        return apis
    
    async def async_get_apis(
        self, 
        region: str, 
    ) -> typing.List[typing.Dict]:
        position = None
        complete = False
        apis = []
        async with AsyncBotoSession().client(
            "apigateway",
            region_name = region, aws_access_key_id = self.aws_access_key_id, aws_secret_access_key = self.aws_secret_access_key
        ) as client:
            while not complete:
                try:
                    gateways = await client.get_rest_apis(limit=self.pagination_limit) \
                                if position is None \
                                else await client.get_rest_apis(limit=self.pagination_limit, position=position)
                except (ClientError, EndpointConnectionError):
                    logger.error(f"Could not get list of APIs in region \"{region}\"")
                    return []
                apis.extend(gateways["items"])
                position = gateways.get("position", None)
                if position is None: complete = True
        return apis
    

    """
    Create Endpoint
    """

    def create_api(
        self, 
        region: str,
    ) -> typing.Optional[str]:

        # We dont do validation
        # since we assume we've done it already
        client = self.get_aws_client(region = region)
        name = self.get_name()
        try:
            api_id = (client.create_rest_api(
                name = name, 
                endpointConfiguration = {"types": ["REGIONAL"]})
            )["id"]

        except (ClientError, EndpointConnectionError):
            logger.error(f"Could not create new API in region \"{region}\"")
            return None
        
        api_resource_id = (client.get_resources(restApiId=api_id))["items"][0]["id"]
        resource_id = (client.create_resource(restApiId=api_id, parentId=api_resource_id, pathPart="{proxy+}"))["id"]
        
        self.configure_api(client, api_id, api_resource_id, resource_id)
        logger.info(f"[{region}] Created API with id \"{api_id}\"")
        endpoint = ProxyEndpoint(
            name = name,
            api_id = api_id,
            region = region
        )
        self.regions_data[region].endpoints.append(endpoint)
        return endpoint

    async def async_create_api(
        self, 
        region: str,
    ) -> typing.Optional[str]:
        # We dont do validation
        # since we assume we've done it already
        async with AsyncBotoSession().client(
            "apigateway",
            region_name = region, aws_access_key_id = self.aws_access_key_id, aws_secret_access_key = self.aws_secret_access_key
        ) as client:
            name = self.get_name()
            try:
                api_id = (await client.create_rest_api(
                    name = name, 
                    endpointConfiguration = {"types": ["REGIONAL"]})
                )["id"]

            except (ClientError, EndpointConnectionError):
                logger.error(f"Could not create new API in region \"{region}\"")
                return None
            api_resource_id = (await client.get_resources(restApiId=api_id))["items"][0]["id"]
            resource_id = (await client.create_resource(restApiId=api_id, parentId=api_resource_id, pathPart="{proxy+}"))["id"]
            
            await self.async_configure_api(client, api_id, api_resource_id, resource_id)
            logger.info(f"[{region}] Created API with id \"{api_id}\"")
            endpoint = ProxyEndpoint(
                name = name,
                api_id = api_id,
                region = region
            )
            self.regions_data[region].endpoints.append(endpoint)
            return endpoint

    
    """
    Configure Endpoints
    """

    def configure_api(
        self, 
        client: typing.Any, 
        api_id: str, 
        api_resource_id: str, 
        resource_id: str
    ) -> None:

        client.put_method(
            restApiId=api_id,
            resourceId=api_resource_id,
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={
                "method.request.path.proxy": True,
                "method.request.header.X-Forwarded-Header": True,
                "method.request.header.X-Host": True,
                "method.request.header.X-User-Agent": True,
            }
        )
        client.put_integration(
            restApiId=api_id,
            resourceId=api_resource_id,
            type="HTTP_PROXY",
            httpMethod="ANY",
            integrationHttpMethod="ANY",
            uri=self.uri,
            connectionType="INTERNET",
            requestParameters={
                "integration.request.path.proxy": "method.request.path.proxy",
                "integration.request.header.X-Forwarded-For": "method.request.header.X-Forwarded-Header",
                "integration.request.header.Host": "method.request.header.X-Host",
                "integration.request.header.User-Agent": "method.request.header.X-User-Agent",
            }
        )
        client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={
                "method.request.path.proxy": True,
                "method.request.header.X-Forwarded-Header": True,
                "method.request.header.X-Host": True,
                "method.request.header.X-User-Agent": True,
            }
        )
        client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            type="HTTP_PROXY",
            httpMethod="ANY",
            integrationHttpMethod="ANY",
            uri=f"{self.uri}/{{proxy}}",
            connectionType="INTERNET",
            requestParameters={
                "integration.request.path.proxy": "method.request.path.proxy",
                "integration.request.header.X-Forwarded-For": "method.request.header.X-Forwarded-Header",
                "integration.request.header.Host": "method.request.header.X-Host",
                "integration.request.header.User-Agent": "method.request.header.X-User-Agent",
            }
        )
        client.create_deployment(
            restApiId=api_id,
            stageName="proxy-stage"
        )
    

    async def async_configure_api(
        self, 
        client: 'AsyncBotoClient', 
        api_id: str, 
        api_resource_id: str, 
        resource_id: str
    ) -> None:
        await client.put_method(
            restApiId=api_id,
            resourceId=api_resource_id,
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={
                "method.request.path.proxy": True,
                "method.request.header.X-Forwarded-Header": True,
                "method.request.header.X-Host": True,
                "method.request.header.X-User-Agent": True,
            }
        )
        await client.put_integration(
            restApiId=api_id,
            resourceId=api_resource_id,
            type="HTTP_PROXY",
            httpMethod="ANY",
            integrationHttpMethod="ANY",
            uri=self.uri,
            connectionType="INTERNET",
            requestParameters={
                "integration.request.path.proxy": "method.request.path.proxy",
                "integration.request.header.X-Forwarded-For": "method.request.header.X-Forwarded-Header",
                "integration.request.header.Host": "method.request.header.X-Host",
                "integration.request.header.User-Agent": "method.request.header.X-User-Agent",
            }
        )
        await client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={
                "method.request.path.proxy": True,
                "method.request.header.X-Forwarded-Header": True,
                "method.request.header.X-Host": True,
                "method.request.header.X-User-Agent": True,
            }
        )
        await client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            type="HTTP_PROXY",
            httpMethod="ANY",
            integrationHttpMethod="ANY",
            uri=f"{self.uri}/{{proxy}}",
            connectionType="INTERNET",
            requestParameters={
                "integration.request.path.proxy": "method.request.path.proxy",
                "integration.request.header.X-Forwarded-For": "method.request.header.X-Forwarded-Header",
                "integration.request.header.Host": "method.request.header.X-Host",
                "integration.request.header.User-Agent": "method.request.header.X-User-Agent",
            }
        )
        await client.create_deployment(
            restApiId=api_id,
            stageName="proxy-stage"
        )

    
    """
    Clear Region APIs
    """

    async def async_clear_region_apis(
        self, 
        region: str,
        force: bool = False,
    ) -> None:
        if not force and self.reuse_gateways:
            logger.warning(f"Skipping clearing region [{region}] APIs ({len(self.regions_data[region].endpoints)}) because `reuse_gateways` = {self.reuse_gateways} and `force` = {force}")
            return
        async with AsyncBotoSession().client(
            "apigateway",
            region_name=region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        ) as client:
            while self.regions_data[region].endpoints:
                api = self.regions_data[region].endpoints.pop()
                try:
                    await client.delete_rest_api(restApiId = api.api_id)
                except ClientError as e:
                    # Add it back in if it fails
                    self.regions_data[region].endpoints.append(api)
                    if e.response["Error"]["Code"] == "TooManyRequestsException":
                        logger.error("Too many requests when deleting rest API, sleeping for 3 seconds")
                        await asyncio.sleep(3.0)
                        return await self.async_clear_region_apis(region)
                logger.info(f"Deleted rest API with id \"{api.api_id}\"")
    
    def clear_region_apis(
        self, 
        region: str,
        force: bool = False,
    ) -> None:
        if not force and self.reuse_gateways:
            logger.warning(f"Skipping clearing region [{region}] APIs ({len(self.regions_data[region].endpoints)}) because `reuse_gateways` = {self.reuse_gateways} and `force` = {force}")
            return
        client = self.get_aws_client(region)
        while self.regions_data[region].endpoints:
            api = self.regions_data[region].endpoints.pop()
            try:
                client.delete_rest_api(restApiId=api.api_id)
            except ClientError as e:
                # Add it back in if it fails
                self.regions_data[region].endpoints.append(api)
                if e.response["Error"]["Code"] == "TooManyRequestsException":
                    logger.error("Too many requests when deleting rest API, sleeping for 3 seconds")
                    time.sleep(3)
                    return self.clear_region_apis(region)
            logger.info(f"Deleted rest API with id \"{api.api_id}\"")
    
    """
    Clear Apis
    """

    def clear_apis(
        self,
        force: bool = False,
    ) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers = settings.num_workers) as executor:
            futures, deleted = [], []
            for region in self.regions_data:
                logger.info(f"[Sync] Clearing all ({len(self.regions_data[region].endpoints)}) created APIs for region {region}")
                futures.append(
                    executor.submit(self.clear_region_apis, region = region, force = force)
                )
            deleted.extend(future.result() for future in concurrent.futures.as_completed(futures))
            logger.info(f"[Sync] All ({len(deleted)}) Regions APIs for ip rotating have been deleted")
    
    async def async_clear_apis(
        self,
        force: bool = False,
    ) -> None:
        tasks = []
        for region in self.regions_data:
            logger.info(f"[Async] Clearing all ({len(self.regions_data[region].endpoints)}) created APIs for region {region}")
            tasks.append(
                asyncio.create_task(self.async_clear_region_apis(region = region, force = force))
            )
        await asyncio.gather(*tasks)
        logger.info(f"[Async] All ({len(tasks)}) Regions APIs for ip rotating have been deleted")
