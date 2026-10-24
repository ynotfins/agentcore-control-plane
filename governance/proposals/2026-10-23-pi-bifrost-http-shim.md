# Proposal: Pi Bifrost HTTP session shim

**Date:** 2026-10-23
**Status:** Applied under AUTH-2026-10-23-PI-BIFROST-HTTP-SHIM
**Rollback:** disable registry entry, remove builder grant, stop 18091, restore host-native fallback

Expose Pi parallel subagents through agentcore-gateway using a Serena-style HTTP session shim.
Do not enable sticky Bifrost STDIO. Do not create a new Windows scheduled task.
