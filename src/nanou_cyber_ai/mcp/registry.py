from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    access: Literal["read", "local_write"]
    required_scope: str


TOOLS: tuple[ToolDescriptor, ...] = (
    ToolDescriptor("cisa.kev.list", "Read the CISA KEV catalog.", "read", "intel:read"),
    ToolDescriptor("nvd.cve.get", "Read a CVE from the NVD API.", "read", "intel:read"),
    ToolDescriptor("malware.metadata.list", "List hashes, labels and static features.",
                   "read", "malware:metadata:read"),
    ToolDescriptor("malware.metadata.add", "Store validated metadata locally.",
                   "local_write", "malware:metadata:write"),
)


class ToolNotAllowed(PermissionError):
    pass


def list_tools() -> list[ToolDescriptor]:
    return list(TOOLS)


def authorize_tool(name: str, scopes: set[str]) -> ToolDescriptor:
    descriptor = next((tool for tool in TOOLS if tool.name == name), None)
    if descriptor is None:
        raise ToolNotAllowed(f"Tool is not registered: {name}")
    if descriptor.required_scope not in scopes:
        raise ToolNotAllowed(f"Missing capability: {descriptor.required_scope}")
    return descriptor
