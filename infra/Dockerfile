# functions base image (infra_002), per docs/decisions/d_infra_001.
# Built on claude-docker; dependencies for individual functions are provisioned at
# RUNTIME from each function's pinned manifest (not baked here).
FROM brunofitas/claude-docker:latest

# Toolchain for the v1 runtimes (bash/python/custom) + JSON I/O helpers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip make jq \
    && rm -rf /var/lib/apt/lists/*

# Volumes mounted by the ContainerManager:
#   /work   shared workspace (fixed root, per run)
#   /lib    function library
#   /cache  shared dependency cache (apt/pip) for fast recreate
WORKDIR /work

# The container idles; the orchestrator drives each step via `docker exec`
# (claude steps use the Claude CLI with the host's plan auth).
CMD ["sleep", "infinity"]
