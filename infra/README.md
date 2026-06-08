# infra

Container runtime + packaging. Currently a placeholder; the base image
(on `brunofitas/claude-docker`) and the container lifecycle manager are built in
`infra_002`, and the cross-platform installers in `infra_003`.

Runtime model sealed in
[`docs/decisions/d_infra_001_container_runtime.md`](../docs/decisions/d_infra_001_container_runtime.md):
fresh-per-run container off a shared base, runtime dependency provisioning from pinned
manifests, shared dep-cache volume, CLI over `docker exec`.
