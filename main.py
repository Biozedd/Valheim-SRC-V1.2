import json
import subprocess
from pathlib import Path
import psutil
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Valheim Server Manager", version="2.1.0")


API_TOKEN = "beman_kar_bedid"
SERVER_DIR = Path(r"C:\ValheimServer")
BAT_FILE = SERVER_DIR / "start_headless_server.bat"
SETTINGS_FILE = Path("settings.json")
PROCESS_NAME = "valheim_server.exe"

DEFAULT_SETTINGS = {
    "name": "My Valheim Server",
    "world": "Dedicated",
    "password": "secretpassword",
    "port": 2456,
    "public": 1,
    "crossplay": True
}


class ServerSettings(BaseModel):
    name: str
    world: str
    password: str
    port: int = 2456
    public: int
    crossplay: bool



def verify_token(authorization: str = Header(None)):
    if authorization != API_TOKEN:
        raise HTTPException(status_code=403, detail="Ramze API eshtebah ast!")



def get_server_process():
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == PROCESS_NAME:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None



def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        saved_data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return {**DEFAULT_SETTINGS, **saved_data}
    except Exception:
        return DEFAULT_SETTINGS


def save_settings(data: dict):
    SETTINGS_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")
    if SERVER_DIR.exists():
        crossplay_flag = "-crossplay" if data.get("crossplay") else ""
        bat_content = (
            "@echo off\n"
            "set SteamAppId=892970\n"
            f'valheim_server -nographics -batchmode -name "{data["name"]}" '
            f'-port {data["port"]} -world "{data["world"]}" '
            f'-password "{data["password"]}" -public {data["public"]} {crossplay_flag}\n'
        )
        BAT_FILE.write_text(bat_content, encoding="utf-8")


@app.get("/api/telemetry", dependencies=[Depends(verify_token)])
def get_telemetry():
    settings = load_settings()
    return {
        "online": get_server_process() is not None,
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "port": settings.get("port", 2456)
    }


@app.get("/api/settings", dependencies=[Depends(verify_token)])
def get_settings():
    return load_settings()


@app.post("/api/settings", dependencies=[Depends(verify_token)])
def update_settings(new_settings: ServerSettings):
    if get_server_process():
        raise HTTPException(status_code=400, detail="Ebteda server ra khamoosh konid!")

    save_settings(new_settings.model_dump())
    return {"message": "Tanzimat ba movafaghiyat zakhire shod"}



@app.post("/api/start", dependencies=[Depends(verify_token)])
def start_server():
    if get_server_process():
        raise HTTPException(status_code=400, detail="Server az ghabl roshan ast!")

    save_settings(load_settings())
    try:
        subprocess.Popen(
            ["cmd.exe", "/c", str(BAT_FILE)],
            cwd=SERVER_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return {"message": "Server ba movafaghiyat roshan shod."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stop", dependencies=[Depends(verify_token)])
def stop_server():
    proc = get_server_process()
    if not proc:
        raise HTTPException(status_code=400, detail="Server dar hale hazer khamoosh ast!")

    try:
        parent = proc.parent()
        proc.kill()
        if parent and parent.name().lower() == "cmd.exe":
            parent.kill()
        return {"message": "Server kamelan baste shod"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/")
def serve_home():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)