"""Web control: drive buttons + live camera stream.

Run on the Pi:      python3 -m robot.web.app
Run on a laptop:    ROBOT_MOCK=1 python3 -m robot.web.app
With the Tapo C210: CAMERA_SOURCE=tapo (and TAPO_* in .env), see docs/tapo-c210.md
Then open http://<pi-hostname>.local:8000 on the phone.
"""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from robot import config
from robot.camera import Camera
from robot.motors import Motors

INDEX_PAGE = Path(__file__).parent / "templates" / "index.html"

app = FastAPI(title="Home Patrol Robot")
hw = {}


@app.on_event("startup")
def startup():
    hw["motors"] = Motors()
    if config.CAMERA_SOURCE == "tapo":
        from robot.tapo import TapoCamera

        hw["camera"] = TapoCamera()
    else:
        hw["camera"] = Camera()


@app.on_event("shutdown")
def shutdown():
    hw["motors"].close()
    hw["camera"].close()


class DriveCommand(BaseModel):
    direction: Literal["forward", "backward", "left", "right", "stop"]


class LookCommand(BaseModel):
    direction: Literal["left", "right", "up", "down"]


@app.get("/")
def index():
    return FileResponse(INDEX_PAGE)


@app.post("/api/drive")
def drive(cmd: DriveCommand):
    hw["motors"].drive(cmd.direction)
    return {"ok": True, "direction": cmd.direction}


@app.post("/api/look")
def look(cmd: LookCommand):
    """Turn the camera (Tapo pan/tilt). The robot itself does not move."""
    camera = hw["camera"]
    if getattr(camera, "pan_tilt", None) is None:
        raise HTTPException(status_code=501, detail="This camera has no pan/tilt")
    try:
        camera.look(cmd.direction)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Pan/tilt failed: {exc}")
    return {"ok": True, "direction": cmd.direction}


@app.get("/api/status")
def status():
    return {
        "moving": hw["motors"].moving,
        "camera": hw["camera"].available,
        "camera_source": config.CAMERA_SOURCE,
        "pan_tilt": getattr(hw["camera"], "pan_tilt", None) is not None,
        "mock": config.MOCK_HARDWARE,
    }


@app.get("/stream.mjpg")
def stream():
    camera = hw["camera"]
    if not camera.available:
        raise HTTPException(status_code=503, detail="Camera not available")

    def mjpeg():
        for frame in camera.frames():
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n"
                + f"Content-Length: {len(frame)}\r\n\r\n".encode()
                + frame
                + b"\r\n"
            )

    return StreamingResponse(mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    import uvicorn

    # One worker only: GPIO pins can be owned by one process.
    uvicorn.run(app, host=config.WEB_HOST, port=config.WEB_PORT)
