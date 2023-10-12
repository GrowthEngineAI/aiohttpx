"""
The CLI Component of the aiohttpx package.
"""


import json
import typer
import asyncio

from pathlib import Path
from typing import Optional, List, Dict, Any, Union


cmd = typer.Typer(no_args_is_help = True)

def build_json_from_string_or_path(string: str) -> bool:
    try:
        return json.loads(string)
    except:
        try:
            return json.loads(Path(string).read_text())
        except:
            return None

def encode_data(data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Encodes the data for the request
    - Ensure that all types are primitive
    """
    for k, v in data.items():
        if isinstance(v, (dict, list, set, tuple, bool, type(None))): data[k] = json.dumps(v)
    return data

async def make_aio_request(
    url: str,
    method: Optional[str] = 'get',
    headers: Optional[str] = None, # These should be a json string or path
    data: Optional[str] = None, # These should be a json string or path
    params: Optional[str] = None, # These should be a json string or path
    
    file: Optional[Union[str, Path]] = None, # this should be a path
    files: Optional[List[Union[str, Path]]] = None, # this should be a list of paths
    output: Optional[Union[str, Path]] = None, # this should be a path
    timeout: Optional[int] = 60,
    no_redirect: Optional[bool] = False,
    verbose: Optional[bool] = False,
) -> None:  # sourcery skip: low-code-quality
    
    if headers: headers = build_json_from_string_or_path(headers)
    if data: data = build_json_from_string_or_path(data)
    if params: params = build_json_from_string_or_path(params)

    request_kwargs = {
        'params': params,
        'headers': headers,
        'timeout': timeout,
        'follow_redirects': not no_redirect,
    }
    if file or files:
        if file:
            input_file = Path(file).resolve()
            request_kwargs['files'] = {'file': (input_file.name, input_file.read_bytes)}
        if files:
            input_files = [Path(f).resolve() for f in files]
            request_kwargs['files'] = [
                ('file', (f.name, f.read_bytes())) for f in input_files
            ]
        if data: request_kwargs['data'] = encode_data(data)

    elif data:
        if method.upper() == 'GET':
            if not request_kwargs['params']: request_kwargs['params'] = {}
            request_kwargs['params'].update(encode_data(data))
        else:
            request_kwargs['json'] = data

    
    from aiohttpx import Client
    from aiohttpx.utils import logger
    c = Client()
    method = method.upper()
    response = await c.async_request(
        method, 
        url, 
        **request_kwargs
    )
    try:
        response.raise_for_status()
    except Exception as e:
        if verbose:
            logger.error(f'Error: {e}\nResponse: {response.text}')
        raise e

    if output:
        output_file = Path(output).resolve()
        output_file.write_bytes(response.content)
        if verbose:
            logger.info(f'Output written to {output_file}')
    else:
        print(response.text)



@cmd.command()
def make_request(
    url: str = typer.Argument(..., help = 'The url to make the request to'),
    method: Optional[str] = typer.Argument('get', help = 'The method to use for the request'),
    headers: Optional[str] = typer.Option(None, '--headers', '-h', help = 'Headers to use for the request. Can be either JSON string or Path'),
    data: Optional[str] = typer.Option(None, '--data', '-d', help = 'Data to use for the request. Can be either JSON string or Path'),
    params: Optional[str] = typer.Option(None, '--params', '-p', help = 'Params to use for the request. Can be either JSON string or Path'),
    
    file: Optional[Path] = typer.Option(None, help = 'A file to upload. Can be either a path or a list of paths'),
    files: Optional[List[Path]] = typer.Option(None, '--files', '-f', help = 'A list of files to upload. Can be either a path or a list of paths'),
    output: Optional[Path] = typer.Option(None, '--output', '-o', help = 'The output file to write the response to. If not provided, will print the response'),
    timeout: Optional[int] = typer.Option(60, help = 'The timeout for the request'),
    no_redirect: Optional[bool] = typer.Option(False,  '--no-redirect', help = 'Whether to disable redirects',),
    verbose: Optional[bool] = typer.Option(False, help = 'Whether to print verbose output'),
):
    """
    Makes a request to the given url
    """
    asyncio.run(
        make_aio_request(
            url = url,
            method = method,
            headers = headers,
            data = data,
            params = params,
            file = file,
            files = files,
            output = output,
            timeout = timeout,
            no_redirect = no_redirect,
            verbose = verbose,
        )
    )


def run_cmd():
    cmd()

if __name__ == '__main__':
    run_cmd()