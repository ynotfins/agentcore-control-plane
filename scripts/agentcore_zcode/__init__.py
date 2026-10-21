"""Host-owned ZCode signed-memory helpers.

ZCode remains Trust Class A on :18082 with no stored builder bearer.
This package signs agentcore-memory tool arguments on the host using the
same DeviceIdentityManager enrollment as Cursor (device.json + keyring),
mirroring scripts/agentcore_devin.
"""

from .signed_memory import (
    CLIENT_KEY,
    DEFAULT_AGENT_KEY,
    HOST_DIRECT_GATEWAY_URL,
    HostSignedZCodeMemoryClient,
    ZCODE_COMPAT_GATEWAY_URL,
    sign_memory_arguments,
)

__all__ = [
    "CLIENT_KEY",
    "DEFAULT_AGENT_KEY",
    "HOST_DIRECT_GATEWAY_URL",
    "HostSignedZCodeMemoryClient",
    "ZCODE_COMPAT_GATEWAY_URL",
    "sign_memory_arguments",
]
