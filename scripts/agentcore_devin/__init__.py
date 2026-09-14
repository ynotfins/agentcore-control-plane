"""Host-owned Devin signed-memory helpers.

Devin remains Trust Class A on :18082 with no stored builder bearer.
This package signs agentcore-memory tool arguments on the host using the
same DeviceIdentityManager enrollment as Cursor (device.json + keyring).
"""

from .signed_memory import (
    CLIENT_KEY,
    DEFAULT_AGENT_KEY,
    DEVIN_COMPAT_GATEWAY_URL,
    HOST_DIRECT_GATEWAY_URL,
    HostSignedMemoryClient,
    sign_memory_arguments,
)

__all__ = [
    "CLIENT_KEY",
    "DEFAULT_AGENT_KEY",
    "DEVIN_COMPAT_GATEWAY_URL",
    "HOST_DIRECT_GATEWAY_URL",
    "HostSignedMemoryClient",
    "sign_memory_arguments",
]
