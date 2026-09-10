# Docker security

Docker provides process isolation, not VM-grade isolation. By default, every container on a host **shares that host's Linux kernel** — a compromised container is one kernel exploit away from affecting the host or other containers, unless the daemon and containers are configured with security in mind. The goal is the **Principle of Least Privilege**: every process gets only the permissions it actually needs, nothing more.

## Security checklist

- [ ] Use official/trusted base images, pinned to a specific version — never `latest` in production.
- [ ] Keep images updated as upstream CVEs are patched.
- [ ] Run as a **non-root user** inside the container.
- [ ] Drop unnecessary Linux **capabilities**; add back only what's required.
- [ ] Scan images regularly (Docker Scout, Trivy, or similar) before deploying.
- [ ] Never hardcode secrets in a Dockerfile or image layer — inject at runtime (env var from a secret manager, Docker/Swarm secret, or mounted file).
- [ ] Use a **read-only root filesystem** where the application allows it.
- [ ] Limit CPU and memory per container (`--cpus`, `--memory`).
- [ ] Prefer signed images from a registry with provenance.
- [ ] Keep the Docker Engine itself updated.

## Run as non-root

```dockerfile
FROM node:20-slim
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app
COPY --chown=appuser:appuser . .
CMD ["node", "server.js"]
```

| Root | Non-root |
|---|---|
| Full permissions inside the container | Limited permissions |
| A container compromise is a bigger blast radius | A compromise is contained to `appuser`'s permissions |
| Can modify OS files | Cannot modify protected files |
| Not recommended | Recommended |

If the process is compromised while running as `appuser` instead of `root`, the attacker inherits `appuser`'s limited permissions, not root — meaningfully raising the bar for privilege escalation.

## Linux capabilities

Root privileges are actually a bundle of dozens of separate **capabilities**. Instead of giving a container full root, grant only the specific capability it needs:

| Capability | Purpose |
|---|---|
| `NET_ADMIN` | Configure network interfaces |
| `NET_BIND_SERVICE` | Bind to ports below 1024 |
| `SYS_ADMIN` | Broad administrative operations — very powerful, avoid if possible |
| `SYS_TIME` | Change system time |
| `CHOWN` | Change file ownership |

```bash
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE nginx
```

## Read-only filesystem

```bash
docker run --read-only --tmpfs /tmp nginx
```

The container's root filesystem becomes immutable; the application can only write to explicitly writable locations (a mounted volume, or a `tmpfs` mount for scratch space). This stops most filesystem-persistence attack techniques outright — there's nowhere for a dropped payload to survive a restart.

## Image scanning

Images can carry known vulnerabilities (CVEs), outdated packages, embedded secrets, or malware in a compromised base layer. Scan before deploying, not after.

**Docker Scout** — Docker's built-in scanning and supply-chain tool: detects CVEs, recommends safer base images, compares versions.

```bash
docker login
docker pull nginx
docker scout cves nginx
```

**Docker Bench for Security** — an open-source script checking the Docker *host and daemon configuration* against the CIS Docker Benchmark (daemon config, host config, containers, images, networking, logging, permissions):

```bash
docker run --rm -it --net host --pid host --userns host --cap-add audit_control \
  -v /etc:/etc:ro \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  docker/docker-bench-security
```

**Trivy** is a common alternative/complement to Docker Scout, widely used in CI pipelines for the same purpose (see `docs/CI_CD_PIPELINE.md` for where a scan step fits in a build pipeline).

## Secrets

Never put a real secret in a Dockerfile `ENV`, `ARG`, or `RUN` instruction — it ends up baked into an image layer, and anyone with `docker history` or a pulled copy of the image can read it back out even if a later layer "removes" it. Inject secrets at runtime instead: Docker/Swarm secrets (mounted at `/run/secrets/`), a secret manager (AWS Secrets Manager, Vault), or environment variables sourced from a secret store at deploy time — never committed to source control.

## Rootless Docker

By default the Docker **daemon itself** runs as root, which means a container escape can, in the worst case, lead to host root. **Rootless Docker** runs `dockerd` as a normal user instead, removing that specific escalation path — an additional hardening layer on top of running individual containers as non-root.

## Interview-ready answers

**Why shouldn't containers run as root?** Root inside a container still carries elevated privileges within that container's namespace; if it's compromised, an attacker has more room to escalate or, in a weakly isolated setup, to affect the host. Non-root limits the blast radius.

**What is the Principle of Least Privilege?** Granting users, applications, and containers only the permissions they need to do their job — no more.

**Why shouldn't secrets go in a Dockerfile?** Anyone with the built image can extract embedded secrets from its layers, even from a layer that appears to delete them later — earlier layers are still present in the image history.

**What's a read-only container?** A container run with an immutable root filesystem; the app can only write to explicitly writable mounts (volumes, `tmpfs`), which blocks most attempts to persist a payload on disk.
