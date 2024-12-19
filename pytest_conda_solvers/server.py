import mimetypes
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status
from fastapi_cache import Coder, FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from pytest import fixture

from .data import get_channel_repodata, load_raw_data_file


class RepodataFilename(str, Enum):
    repodata = "repodata.json"
    current_repodata = "current_repodata.json"


class ChannelServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def get_base_url(self):
        return f"http://{self.host}:{self.port}"

    def get_channel_url(self, channel):
        return f"{self.get_base_url()}/{channel}"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


class NullCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return value

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return value


@fixture(scope="session")
def channel_server(host="localhost", port=8080):
    app = FastAPI(lifespan=lifespan)

    @app.get("/conda_format_repo/{full_path:path}")
    @cache(coder=NullCoder)
    async def conda_format_repo_contents(full_path: str):
        path = Path(f"conda_format_repo/{full_path}")
        data = load_raw_data_file(path)
        mimetype = mimetypes.guess_type(path)[0]
        return Response(data, media_type=mimetype)

    @app.get("/{channel_name}/{subdir}/{filename}")
    @cache()
    async def repodata(
        channel_name: str,
        subdir: str,
        filename: RepodataFilename,
    ):
        return get_channel_repodata(channel_name, subdir, filename.value)

    @app.get("/{full_path:path}")
    async def catch_all():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={
            "host": host,
            "port": port,
        },
        daemon=True,
    )
    thread.start()

    yield ChannelServer(host, port)
