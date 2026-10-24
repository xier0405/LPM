import re

def validate_command(command: str) -> bool:
    """只允許 LPM 自己會使用的套件管理相關指令。"""

    dangerous_patterns = [
        r"`",
        r"\$\(",
        r">",
        r"<",
        r";",
        r"\n",
        r"\r",
        r"(?<!&)&(?!&)",  # ✨ 核心防禦 1：阻擋單一的 & (背景執行)，但完美放行 &&
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return False

    allowed_commands = {
        "apt",
        "apt-get",
        "pacman",
        "yay",
        "paru",
        "snap",
        "flatpak",
        "dnf",
        "zypper",
        "apk",
        "emerge",
        "xbps-install",
        "xbps-remove",
        "brew",
        "echo",
        "true",
    }

    normalized = re.sub(r"[()]", " ", command)
    # ✨ 核心防禦 2：把單一的 & 也納入切割器，確保任何越界的惡意指令都會被送去白名單檢驗而落網！
    segments = re.split(r"\s*(?:&&|\|\||\||&)\s*", normalized)

    for segment in segments:
        segment = segment.strip()

        if not segment:
            continue

        segment = re.sub(
            r"^sudo(?:\s+-S)?\s+",
            "",
            segment
        )

        parts = segment.split()

        if not parts:
            continue

        executable = parts[0]

        if executable not in allowed_commands:
            return False

    return True