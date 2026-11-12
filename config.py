"""Persist non-secret preferences; credentials belong in the OS keyring only."""

import json
import os
from pathlib import Path
import secrets
import stat
from dataclasses import asdict, dataclass


class ConfigError(Exception):
    """A safe, user-facing settings error (never include file contents)."""


@dataclass(frozen=True)
class Settings:
    version: int = 1
    ai_engine: str = "gemini"
    ssh_mode: bool = False
    preferred_mgr: str = "apt"
    remember_token: bool = True
    left_pane_width: int = 40
    bottom_pane_height: int = 60
    current_sort: str = "name"
    sort_descending: bool = False
    current_priority_manager: str = "apt"

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ConfigError("設定檔格式錯誤；請修復或移走 config.json 後重試。")
        version = data.get("version", 1)
        if type(version) is not int or version != 1:
            raise ConfigError("不支援此設定檔版本；請修復或移走 config.json 後重試。")
        defaults = asdict(cls())
        managers = {"apt", "pacman", "yay", "paru", "dnf", "zypper", "apk",
                    "emerge", "xbps", "snap", "flatpak", "brew"}
        choices = {
            "ai_engine": {"gemini"},
            "preferred_mgr": managers,
            "current_priority_manager": managers,
            "current_sort": {"manager", "name", "group", "version", "size"},
        }
        limits = {"left_pane_width": (20, 70), "bottom_pane_height": (20, 80)}
        # Whitelist fields, exact types and ranges. Unknown/secret fields are discarded.
        for key, default in defaults.items():
            value = data.get(key, default)
            if type(value) is not type(default):
                continue
            if key in choices and value not in choices[key]:
                continue
            if key in limits and not limits[key][0] <= value <= limits[key][1]:
                continue
            defaults[key] = value
        return cls(**defaults)


class ConfigStore:
    def __init__(self, directory=None):
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".config"
        self.directory = Path(directory) if directory is not None else base / "lpm"
        self.warning = None
        self._read_failed = False

    def _open_directory(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if os.fstat(fd).st_uid != os.getuid():
                raise OSError("Settings directory has a different owner")
            os.fchmod(fd, 0o700)
            return fd
        except BaseException:
            os.close(fd)
            raise

    @staticmethod
    def _check_file(directory_fd):
        try:
            info = os.stat("config.json", dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise OSError("Settings must be an owned regular file")

    def load(self):
        directory_fd = None
        try:
            if not self.directory.exists() and not self.directory.is_symlink():
                return Settings()
            directory_fd = self._open_directory()
            self._check_file(directory_fd)
            try:
                fd = os.open("config.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=directory_fd)
            except FileNotFoundError:
                return Settings()
            with os.fdopen(fd, "r", encoding="utf-8") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                    raise OSError("Invalid settings file")
                os.fchmod(stream.fileno(), 0o600)
                raw = stream.read(65537)
                if len(raw) > 65536:
                    raise ConfigError("設定檔過大；請修復或移走 config.json 後重試。")
                return Settings.from_dict(json.loads(raw))
        except (OSError, ValueError, ConfigError):
            self._read_failed = True
            self.warning = "設定檔無法讀取，已使用預設值；為保留原檔，暫停儲存，請檢查 config.json。"
            return Settings()
        finally:
            if directory_fd is not None:
                os.close(directory_fd)

    def save(self, settings):
        if self._read_failed:
            raise ConfigError(self.warning)
        directory_fd = None
        temporary = None
        try:
            # Even a caller-created Settings instance must pass the whitelist.
            clean = Settings.from_dict(asdict(settings))
            payload = json.dumps(asdict(clean), ensure_ascii=False, indent=2) + "\n"
            directory_fd = self._open_directory()
            self._check_file(directory_fd)
            temporary = ".config-" + secrets.token_hex(16)
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory_fd)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, "config.json", src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            temporary = None
            os.fsync(directory_fd)
        except (OSError, ValueError, TypeError):
            raise ConfigError("設定無法儲存；請檢查設定目錄的權限與可用空間。") from None
        finally:
            if directory_fd is not None:
                if temporary is not None:
                    try:
                        os.unlink(temporary, dir_fd=directory_fd)
                    except FileNotFoundError:
                        pass
                os.close(directory_fd)


class SecretStoreError(Exception):
    """Do not attach backend exceptions: they may contain credentials."""


class TokenStore:
    SERVICE = "io.github.xier0405.LPM"
    ACCOUNT = "gemini-api-token"

    def _backend(self):
        # Explicit backend: never auto-select a plaintext/third-party fallback.
        from keyring.backends.SecretService import Keyring
        return Keyring()

    def load(self):
        try:
            return self._backend().get_password(self.SERVICE, self.ACCOUNT) or ""
        except Exception:
            raise SecretStoreError("無法存取系統金鑰圈；請確認 Secret Service 已啟動且已解鎖。") from None

    def save(self, token):
        try:
            self._backend().set_password(self.SERVICE, self.ACCOUNT, token)
        except Exception:
            raise SecretStoreError("Token 未能儲存至金鑰圈；目前只會在本次執行使用。") from None

    def delete(self):
        try:
            backend = self._backend()
            if backend.get_password(self.SERVICE, self.ACCOUNT) is not None:
                backend.delete_password(self.SERVICE, self.ACCOUNT)
        except Exception:
            raise SecretStoreError("無法刪除金鑰圈中的 Token；請解鎖金鑰圈後重試。") from None
