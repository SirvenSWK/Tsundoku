import json
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from tsundoku.models.storage_paths import data_directory, migrate_legacy_file

load_dotenv()

# Set this to the deployed Vercel endpoint for a distributed demo build.
DEFAULT_AI_PROXY_URL = ""

LEGACY_SETTINGS_FILE = (
    Path(__file__).resolve().parent.parent / "Data" / "settings.json"
)
SETTINGS_FILE = data_directory() / "settings.json"


def saveApiKey(apiKey: str) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporaryPath = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=SETTINGS_FILE.parent,
            prefix="settings.", suffix=".tmp", delete=False,
        ) as file:
            temporaryPath = Path(file.name)
            json.dump({"apiKey": apiKey}, file, indent=4)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporaryPath, SETTINGS_FILE)
    finally:
        if temporaryPath is not None and temporaryPath.exists():
            temporaryPath.unlink()


def loadApi() -> str | None:
    environmentApiKey = os.getenv("GROQ_API_KEY")

    if environmentApiKey:
        return environmentApiKey

    migrate_legacy_file(LEGACY_SETTINGS_FILE, SETTINGS_FILE)
    if not SETTINGS_FILE.exists():
        return None

    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("apiKey")


def loadAiProxyUrl() -> str | None:
    value = os.getenv("TSUNDOKU_AI_PROXY_URL", DEFAULT_AI_PROXY_URL).strip()
    return value or None


def hasAiAccess() -> bool:
    return bool(loadAiProxyUrl() or loadApi())
