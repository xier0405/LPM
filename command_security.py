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
    segments = re.split(r"\s*(?:&&|\|\||\|)\s*", normalized)

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