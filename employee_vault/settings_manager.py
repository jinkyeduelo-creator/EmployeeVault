from __future__ import annotations
import os, sys, configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

APP_NAME = "EmployeeVault"
INI_BASENAME = "settings.ini"

def _platform_config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / ".config" / APP_NAME

def default_ini_path() -> Path:
    return _platform_config_dir() / INI_BASENAME

@dataclass
class NetworkConfig:
    server_pc: str = ""
    share_name: str = ""
    enable_lock: bool = False
    username: str = ""

class SettingsStore:
    def __init__(self, ini_path: Optional[Path] = None) -> None:
        self.ini_path = Path(ini_path or default_ini_path())
        self.cfg = configparser.ConfigParser()

    @classmethod
    def load_default(cls) -> "SettingsStore":
        store = cls()
        store.load()
        return store

    def load(self) -> None:
        self.cfg.clear()
        if self.ini_path.exists():
            self.cfg.read(self.ini_path, encoding="utf-8")

    def save(self) -> None:
        self.ini_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ini_path.open("w", encoding="utf-8") as f:
            self.cfg.write(f)

    def get_network(self) -> NetworkConfig:
        s = self.cfg["network"] if self.cfg.has_section("network") else {}
        def _b(v: str) -> bool:
            return str(v).strip().lower() in {"1","true","yes","on"}
        return NetworkConfig(
            server_pc=s.get("server_pc",""),
            share_name=s.get("share_name",""),
            enable_lock=_b(s.get("enable_lock","false")),
            username=s.get("username",""),
        )

    def update_network(self, server_pc: str, share_name: str, enable_lock: bool, username: str = "") -> None:
        if not self.cfg.has_section("network"):
            self.cfg.add_section("network")
        self.cfg.set("network","server_pc",(server_pc or "").strip())
        self.cfg.set("network","share_name",(share_name or "").strip())
        self.cfg.set("network","enable_lock","true" if enable_lock else "false")
        self.cfg.set("network","username",(username or "").strip())

def bootstrap_settings():
    store = SettingsStore.load_default()
    return store, store.get_network()

def resolve_network_lock(env_override: str | None, ini_value: bool) -> bool:
    def _b(v: str) -> bool:
        return str(v).strip().lower() in {"1","true","yes","on"}
    if env_override is None:
        return bool(ini_value)
    return _b(env_override)
