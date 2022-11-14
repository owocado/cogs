from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ResponseInfo:
    url: str = ""
    content_type: str = ""
    http_code: int = 0
    redirect_url: str = ""
    primary_ip: str = ""
    primary_port: int = 0
    local_ip: str = ""
    local_port: int = 0

    @classmethod
    def from_data(cls, data: dict) -> ResponseInfo:
        return cls(
            url=data.pop('url', ''),
            content_type=data.pop('content_type', ''),
            http_code=data.pop('http_code', 0),
            redirect_url=data.pop('redirect_url', ''),
            primary_ip=data.pop('primary_ip', ''),
            local_ip=data.pop('local_ip', ''),
            primary_port=data.pop('primary_port', 0),
            local_port=data.pop('local_port', 0)
        )


@dataclass
class RedirectChecker:
    result: str = ""
    error: bool = False
    data: List[ResponseInfo] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict) -> RedirectChecker:
        data_array = [x.get('response', {}).get('info', {}) for x in data.pop('data', [])]
        return cls(
            result=data.pop('result', ''),
            error=data.pop('error', False),
            data=[ResponseInfo.from_data(x) for x in data_array]
        )
