import re


# 只允許這些字元出現在套件名稱中。
# 不允許 Shell 變數、萬用字元及特殊控制符號。
PACKAGE = r"[A-Za-z0-9][A-Za-z0-9@._+:-]*"
PACKAGES = rf"{PACKAGE}(?: {PACKAGE})*"


# 不需要指定套件名稱的固定指令
FIXED_COMMANDS = {
    "sudo apt update",
    "sudo apt upgrade -y",
    "sudo apt autoremove -y",
    "sudo apt autoclean",

    "sudo pacman -Syu --noconfirm",
    "yay -Syu --noconfirm",
    "yay -Yc --noconfirm",
    "paru -Syu --noconfirm",
    "paru -c --noconfirm",

    "sudo snap refresh",
    "flatpak update -y",
    "flatpak uninstall --unused -y",

    "sudo dnf upgrade -y",
    "sudo dnf autoremove -y",
    "sudo zypper update -y",

    "sudo apk update",
    "sudo apk upgrade",

    # 安裝 snapd 後的固定設定指令
    "sudo systemctl enable --now snapd.socket",
    "sudo ln -sf /var/lib/snapd/snap /snap",

    # 僅供下方已知 Pacman 清理流程使用
    "__PACMAN_ORPHANS__",
}


# 可以接上套件名稱的指令格式
PACKAGE_COMMAND_PREFIXES = (
    "sudo apt install -y",
    "sudo apt purge -y",
    "sudo apt --only-upgrade install -y",

    "sudo pacman -S --noconfirm",
    "sudo pacman -S --needed --noconfirm",
    "sudo pacman -Rns --noconfirm",
    "sudo pacman -Rns",

    "yay -S --noconfirm",
    "yay -S --needed --noconfirm",
    "yay -Rns --noconfirm",
    "yay -Rns",

    "paru -S --noconfirm",
    "paru -S --needed --noconfirm",
    "paru -Rns --noconfirm",
    "paru -Rns",

    "sudo snap install",
    "sudo snap remove",
    "sudo snap refresh",

    "flatpak install -y",
    "flatpak uninstall -y",
    "flatpak update -y",

    "sudo dnf install -y",
    "sudo dnf remove -y",
    "sudo dnf upgrade -y",

    "sudo zypper install -y",
    "sudo zypper remove -y",
    "sudo zypper update -y",

    "sudo apk add",
    "sudo apk del",
    "sudo apk add --upgrade",

    "sudo emerge --deselect",
    "sudo xbps-remove -R",
    "brew uninstall",
)


# 將允許的格式編譯成正規表示式
PACKAGE_COMMANDS = tuple(
    re.compile(re.escape(prefix) + " " + PACKAGES)
    for prefix in PACKAGE_COMMAND_PREFIXES
)


# Snap 安裝失敗時使用 Classic 模式重試
SNAP_INSTALL_RETRY = re.compile(
    rf"sudo snap install (?P<pkgs>{PACKAGES}) \|\| "
    r"\(echo '⚠️ LPM 偵測到套件需要 Classic 沙盒權限，正在自動為您重試\.\.\.'"
    r" && sudo snap install (?P=pkgs) --classic\)"
)


# Snap 移除失敗時使用 purge 重試
SNAP_REMOVE_RETRY = re.compile(
    rf"sudo snap remove (?P<pkgs>{PACKAGES}) \|\| "
    r"\(echo '⚠️ 偵測到殘留的套件設定檔，正在啟動強制清除\.\.\.'"
    r" && sudo snap remove (?P=pkgs) --purge\)"
)


# Pacman 清理孤兒套件的固定指令
PACMAN_ORPHANS = (
    "(pacman -Qdtq | sudo pacman -Rns - || true)"
)


def validate_command(command: str) -> bool:
    """只接受 LPM 已知的套件管理指令格式。"""

    # 第一層：檢查資料型態及長度
    if not isinstance(command, str):
        return False

    if not command or len(command) > 32768:
        return False

    # 第二層：辨識 LPM 內建的特殊重試流程
    # 注意：這裡只是在驗證用的字串中進行替換，
    # 並沒有改變真正要執行的指令。
    normalized = SNAP_INSTALL_RETRY.sub(
        lambda match: f"sudo snap install {match['pkgs']}",
        command
    )

    normalized = SNAP_REMOVE_RETRY.sub(
        lambda match: f"sudo snap remove {match['pkgs']}",
        normalized
    )

    normalized = normalized.replace(
        PACMAN_ORPHANS,
        "__PACMAN_ORPHANS__"
    )

    # 第三層：只允許使用 && 串接合法指令
    steps = normalized.split(" && ")

    # 第四層：每個指令都必須符合允許清單
    return all(
        step in FIXED_COMMANDS
        or any(
            pattern.fullmatch(step)
            for pattern in PACKAGE_COMMANDS
        )
        for step in steps
    )