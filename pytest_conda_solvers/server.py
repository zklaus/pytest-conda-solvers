import json
import threading
from enum import Enum
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException, Response, status
from pytest import fixture

from .data import get_channel_repodata


class RepodataFilename(str, Enum):
    repodata = "repodata.json"
    current_repodata = "current_repodata.json"


class ChannelServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def get_channel_url(self, channel):
        return f"http://{self.host}:{self.port}/{channel}"


@lru_cache(maxsize=None)
def _get_encoded_channel_repodata(channel_name, subdir, filename):
    return json.dumps(get_channel_repodata(channel_name, subdir, filename))


@fixture(scope="session")
def channel_server(host="localhost", port=8080):
    app = FastAPI()

    @app.get("/{channel_name}/{subdir}/{filename}")
    async def repodata(
        channel_name: str,
        subdir: str,
        filename: RepodataFilename,
    ):
        return Response(
            _get_encoded_channel_repodata(channel_name, subdir, filename.value),
            media_type="application/json",
        )

    @app.get("/{full_path:path}")
    async def catch_all():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": host, "port": port},
        daemon=True,
    )
    thread.start()

    yield ChannelServer(host, port)
