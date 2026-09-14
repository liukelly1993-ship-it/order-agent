"""运行环境相关的小型辅助函数。"""

import os
from urllib.parse import urlsplit, urlunsplit


def resolve_service_url(url: str | None) -> str | None:
    """在容器中保留 URL 凭据，仅替换本地服务主机名。"""
    host_override = os.getenv("SERVICE_HOST_OVERRIDE")
    if not url or not host_override:
        return url

    parsed = urlsplit(url)
    hostname = parsed.hostname
    if hostname not in {"localhost", "127.0.0.1", "::1"}:
        return url

    netloc = parsed.netloc.replace(hostname, host_override, 1)
    return urlunsplit(parsed._replace(netloc=netloc))
