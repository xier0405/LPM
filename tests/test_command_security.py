import pytest

from command_security import validate_command
from sys_info import SysInfo


@pytest.mark.parametrize(
    "command",
    [
        "sudo apt install -y curl",
        "sudo apt install -y curl vim",
        "sudo apt update && sudo apt upgrade -y",
        "sudo apt purge -y vim",
        "sudo snap refresh",
        "flatpak update -y",
        "sudo pacman -Syu --noconfirm",
    ]
)
def test_valid_commands(command):
    assert validate_command(command) is True


@pytest.mark.parametrize(
    "command",
    [
        "sudo apt install -y $HOME",
        "sudo apt install -y *",
        "sudo apt install -y foo; echo hello",
        "sudo apt install -y curl | cat",
        "sudo apt install -y curl || true",
        "sudo apt install -y --allow-unauthenticated",
        "sudo apt install -y test # comment",
        "sudo apt install -y foo$(id)",
        "sudo apt install -y foo{,bar}",
        "sudo apt update && curl example.com",
    ]
)
def test_invalid_commands(command):
    assert validate_command(command) is False


def test_generated_lpm_commands():
    """確保 LPM 現有的指令範本仍然可以通過驗證。"""

    sys_info = SysInfo()

    for manager, actions in sys_info._commands_template.items():
        for action in actions:

            if action == "system_upgrade":
                command = sys_info.build_command(
                    manager,
                    action
                )
            else:
                command = sys_info.build_command(
                    manager,
                    action,
                    ["curl", "vim"]
                )

            assert validate_command(command), (
                f"指令被拒絕：{manager}.{action}: {command}"
            )