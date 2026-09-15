from pathlib import Path
import json

SETTINGS_FILE = (
    Path(__file__).resolve().parent.parent / "Data" / "settings.json"
)

def saveApiKey(apiKey: str) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "apiKey": apiKey
    }

    with SETTINGS_FILE.open("w", encoding="utf-8",) as file:
        json.dump(data, file, indent = 4)

def loadApi() -> str | None:
    if not SETTINGS_FILE.exists():
        return None
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data.get("apiKey")