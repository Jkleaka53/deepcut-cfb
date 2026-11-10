"""CollegeFootballData API client with a simple on-disk JSON cache."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import requests

from cfbm import config


class CfbdError(RuntimeError):
    pass


class CfbdClient:
    def __init__(self, api_key: str, cache_dir: Path, base_url: str = config.CFBD_BASE_URL):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")
        self.calls_made = 0
        self._session = requests.Session()

    def _cache_path(self, path: str, params: dict) -> Path:
        key = path + json.dumps(sorted((str(k), str(v)) for k, v in params.items()))
        return self.cache_dir / (hashlib.sha1(key.encode()).hexdigest() + ".json")

    def get(self, path: str, params: dict, *, cacheable: bool = True) -> list | dict:
        cache_file = self._cache_path(path, params)
        if cacheable and cache_file.exists():
            return json.loads(cache_file.read_text())

        resp = self._session.get(
            self.base_url + path,
            params=params,
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            timeout=60,
        )
        self.calls_made += 1
        if not resp.ok:
            raise CfbdError(f"CFBD {resp.status_code} on {path} {params}")
        data = resp.json()
        cache_file.write_text(json.dumps(data))
        return data
