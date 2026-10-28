# Cherry Studio — AgentCore Gateway Enrollment Status

AgentCore gateway enrollment is **unsupported/unverified** for Cherry Studio.
Cherry Studio persists remote MCP headers in Local Storage LevelDB and does not
provide an approved environment-backed header or process-attested AgentCore route.

Do not run the historical enrollment script and do not paste or persist an
AgentCore virtual key in Cherry Studio. The repository template is deliberately
inactive until a credential-free, native-token, or scoped-broker route is approved.

The July 2026 credential-bearing LevelDB enrollment and its validation evidence are
preserved as **legacy drift**. This source reconciliation does not inspect, remove,
or modify that live state. Any cleanup requires a separate backup-first client task.

Cherry Studio may continue to use its host-native features without AgentCore gateway
enrollment. Its Global Memory and builtin in-memory MCP services do not become an
AgentCore memory authority.
