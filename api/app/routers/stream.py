import asyncio
from pathlib import Path

from fastapi import APIRouter, WebSocket

from ..core.config import get_settings

router = APIRouter(prefix="/logs", tags=["logs"])


@router.websocket("/stream")
async def stream_logs(ws: WebSocket):
    await ws.accept()
    settings = get_settings()
    path = Path(settings.LOG_FILE_PATH)
    if not path.exists():
        await ws.close(code=1000)
        return
    with path.open("r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                await ws.send_text(line.rstrip())
            else:
                await asyncio.sleep(0.5)
