from dataclasses import dataclass


@dataclass
class Package:
    manager: str
    name: str
    version: str = "未知"
    size: str = "未知"
    group: str = "System"