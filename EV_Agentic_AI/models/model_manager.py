"""Small model registry built on joblib and optional Keras."""

from __future__ import annotations

from pathlib import Path
import pickle
from typing import Any

try:
    import joblib
except Exception:  # pragma: no cover - fallback for minimal runtimes
    joblib = None

from config.settings import settings


class ModelManager:
    def __init__(self, model_dir: Path | str = settings.model_dir) -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str, suffix: str = ".joblib") -> Path:
        return self.model_dir / f"{name}{suffix}"

    def save_sklearn(self, name: str, model: Any) -> Path:
        path = self.path(name)
        if joblib is not None:
            joblib.dump(model, path)
        else:
            with path.open("wb") as handle:
                pickle.dump(model, handle)
        return path

    def load_sklearn(self, name: str) -> Any | None:
        path = self.path(name)
        if not path.exists():
            return None
        if joblib is not None:
            return joblib.load(path)
        with path.open("rb") as handle:
            return pickle.load(handle)
