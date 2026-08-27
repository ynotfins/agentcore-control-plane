FROM public.ecr.aws/e0h8a4b6/devin-cli:stable

# Bounded Outpost worker image for AgentCore PC layout.
# Binds belong on I:/LocalApps/Devin/outpost-worker — not F: or H: production trees.

USER root
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Default command starts the Devin CLI worker.
# Auth token must come from the host User-scope environment at runtime (never bake secrets into the image).
CMD ["worker", "start"]
