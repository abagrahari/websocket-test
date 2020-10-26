from typing import Final
import asyncio
from pathlib import Path
import logging
import json
import weakref

import aiohttp
from aiohttp import web, WSCloseCode
import numpy as np

app = web.Application()
app["websockets"] = weakref.WeakSet()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)-12s: %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
    force=True,
)
logging.getLogger("asyncio").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

DTYPE: Final[str] = "float32"
# assumes float32 data is sent in binary

# https://docs.aiohttp.org/en/stable/web_advanced.html#graceful-shutdown
async def on_shutdown(app):
    for ws in set(app["websockets"]):
        await ws.close(code=WSCloseCode.GOING_AWAY, message="Server shutdown")


async def websocket_handler(
    request: aiohttp.web_request.Request,
) -> web.WebSocketResponse:

    # Setup websocket
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app["websockets"].add(ws)

    msg: aiohttp.WSMessage
    try:
        async for msg in ws:
            logger.info(
                "Type:%s, Msg: %r, type(msg.data):%s",
                msg.type,
                msg.data,
                type(msg.data),
            )
            if msg.type == aiohttp.WSMsgType.TEXT:
                _, _ = json.loads(msg.data)
                return_kwargs = {"accepted": True}
                return_json = json.dumps(["created", return_kwargs])
                await ws.send_str(return_json)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                received = np.fromstring(msg.data, dtype=DTYPE)
                received += 1
                await ws.send_bytes(received.tobytes())
            await asyncio.sleep(0.7)
    except Exception as e:
        logger.exception("Error during websocket communication: %s", e)
    finally:
        request.app["websockets"].discard(ws)
        logger.debug("websocket connection closed")
    return ws


app.on_shutdown.append(on_shutdown)
app["websockets"] = weakref.WeakSet()  # list of websocket objects
app.add_routes([web.get("/ws", websocket_handler)])
logger.info("Starting server")
if __name__ == "__main__":
    web.run_app(app, host="localhost", port=8080)
logger.info("Shutting down server...")
