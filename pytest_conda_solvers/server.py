from enum import Enum
import threading

from fastapi import FastAPI
from pytest import fixture
import uvicorn

from .data import get_channel_repodata


class RepodataFilename(str, Enum):
    repodata = "repodata.json"
    current_repodata = "current_repodata.json"


class ChannelServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def get_channel_url(self, channel, subdir):
        return f"http://{self.host}:{self.port}/{channel}/{subdir}"


@fixture(scope="session")
def channel_server(host="localhost", port=8080):
    app = FastAPI()

    @app.get("/{channel_name}/{subdir}/{filename}")
    async def repodata(
        channel_name: str,
        subdir: str,
        filename: RepodataFilename,
    ):
        return get_channel_repodata(channel_name, subdir, filename.value)

    thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": host, "port": port},
        daemon=True,
    )
    thread.start()

    yield ChannelServer(host, port)
