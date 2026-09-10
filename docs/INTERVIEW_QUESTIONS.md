# Interview questions

## Fundamentals

**1. What's the difference between a physical server, a VM, and a container?**
A physical server is dedicated hardware. A VM emulates hardware and runs its own full guest OS under a hypervisor. A container shares the host's Linux kernel and packages only the application plus its dependencies — no separate kernel, which is why it starts in milliseconds instead of tens of seconds.

**2. What is a Docker image?**
A read-only template containing the application, runtime, libraries, dependencies, and configuration needed to create containers.

**3. What is the difference between an image and a container?**
An image is a static, read-only blueprint. A container is a running (or stopped) writable instance created from that image.

**4. What are Docker components?**
Docker Client (CLI), Docker Host (where the daemon runs), Docker Daemon (`dockerd`, manages images/containers/networks/volumes), Docker Registry (stores images).

**5. What is OCI?**
The Open Container Initiative — an open standard (Linux Foundation, 2015) defining the Image Specification and Runtime Specification so images and runtimes are portable across Docker, containerd, CRI-O, and Podman.

## Dockerfile

**6. CMD vs. ENTRYPOINT?**
`CMD` sets default arguments and is easily overridden by anything passed after the image name in `docker run`. `ENTRYPOINT` is the fixed main executable — arguments after the image name are appended to it, not substituted, unless `--entrypoint` is used explicitly.

**7. COPY vs. ADD?**
`COPY` copies local files/directories into the image — simple and predictable. `ADD` does the same but also fetches remote URLs and auto-extracts local tar archives; `COPY` is preferred unless you specifically need one of those extras.

**8. ENV vs. ARG?**
`ARG` is a build-time-only variable, not present in the running container by default. `ENV` is set during build and remains available at runtime.

**9. What does EXPOSE actually do?**
Documents which port the application listens on. It does not publish the port — only `-p`/`--publish` at `docker run` time (or `ports:` in Compose) does that.

**10. What causes Docker build cache invalidation?**
A changed Dockerfile instruction, or changed inputs to that instruction (e.g., a `COPY` source file changed). Once one layer's cache is invalidated, every layer after it rebuilds too — which is why dependency installs should come before application code in the Dockerfile.

**11. What is a multi-stage build, and why use one?**
A Dockerfile with multiple `FROM` stages — one builds the app with full tooling, the final stage copies only the built artifact via `COPY --from=<stage>` into a minimal runtime image. Produces smaller, more secure images with no leaked build tools or source.

**12. Why should `COPY requirements.txt` / `package.json` come before copying the rest of the source?**
Dependencies change far less often than application code. Installing them first lets Docker reuse that cached layer on most rebuilds, so only the fast final `COPY . .` (and anything after it) needs to rerun.

## Storage & networking

**13. Named volume vs. bind mount?**
Named volume: Docker-managed, stored under `/var/lib/docker/volumes/`, best for persistent app data (databases, Jenkins home). Bind mount: maps a specific host directory straight into the container — best for local development and live config/source editing.

**14. What is tmpfs?**
A mount backed by host RAM, not disk. Data disappears when the container stops — good for caches or data that must never be written to disk.

**15. Default bridge vs. a user-defined bridge network?**
Default bridge: containers reach each other by IP only. User-defined bridge: built-in DNS lets containers resolve each other by **container name** — the reason Compose always creates its own network.

**16. What's an overlay network for?**
Connecting containers across multiple Docker hosts as if they shared one network — the backbone of Swarm service networking.

**17. When would you use host networking?**
When you need maximum throughput and can accept reduced isolation and no port remapping — e.g., a monitoring agent or high-performance network service.

## Compose & Swarm

**18. Docker Compose vs. Docker Swarm?**
Compose orchestrates multiple containers on a **single host** from one YAML file. Swarm manages a **multi-host cluster**, adding replication, self-healing, rolling updates, and overlay networking. A Stack deploys Compose-syntax onto a Swarm cluster with `docker stack deploy`.

**19. What is a replica?**
One running instance (task) of a service. Multiple replicas give horizontal scaling and resilience against node or container failure.

**20. Replicated vs. global service?**
Replicated: you specify a total replica count, distributed across available nodes (not guaranteed one per node). Global: exactly one task runs on every node automatically — used for per-node agents like log collectors.

**21. What is a rolling update, and how do you roll one back?**
Gradually replacing a service's replicas with a new image version so the service stays available throughout. `docker service update --image <new-image> <service>` performs it; `docker service rollback <service>` reverts to the prior version.

**22. What are Docker Swarm secrets?**
Encrypted-at-rest sensitive values (passwords, keys, certs) made available only to the services that request them, mounted read-only at `/run/secrets/<name>` — the correct alternative to hardcoding secrets in an image or Compose environment variable.

## Security

**23. Why shouldn't containers run as root?**
Root inside a container still carries elevated privileges within its namespace; a compromise gives an attacker a bigger blast radius. Non-root limits what a compromised process can do.

**24. What are Linux capabilities, and why does Docker let you drop/add them?**
Root privileges split into fine-grained units (`NET_ADMIN`, `SYS_ADMIN`, `CHOWN`, etc.). Dropping all and adding back only what's needed (`--cap-drop ALL --cap-add NET_BIND_SERVICE`) follows least privilege instead of granting full root.

**25. Why shouldn't secrets be embedded in a Dockerfile?**
Anyone with the built image can extract secrets from its layer history, even from a layer that appears to delete them later in the file — earlier layers persist in the image.

**26. What is Docker Scout / Docker Bench for Security?**
Docker Scout scans images for CVEs and recommends safer base images/versions. Docker Bench for Security checks the Docker **host and daemon configuration** against the CIS Docker Benchmark. Trivy is a common alternative/complement to Scout in CI pipelines.

## Architect / SRE level

**27. Walk through what happens when you run `docker run nginx`.**
The client sends the request to the daemon over the REST API. The daemon checks for the image locally; if absent, it pulls from the configured registry. It then creates the container — setting up namespaces and cgroups, attaching networking, adding the writable layer — and `containerd`/`runc` start the process defined by `ENTRYPOINT`/`CMD`.

**28. How do namespaces and cgroups actually provide isolation and limits?**
Namespaces (PID, NET, MNT, etc.) give each container its own view of processes, network interfaces, and mounts, so containers can't see each other's resources. cgroups enforce CPU/memory/I-O limits so one container can't starve the host or other containers. Neither is a hypervisor — both are Linux kernel features, which is why containers are lightweight compared to VMs.

**29. How would you reduce a production image's size and attack surface?**
Smaller base image (alpine/slim, or distroless), multi-stage builds, combined `RUN` layers with cache cleanup in the same layer, `.dockerignore`, pinned versions instead of `latest`, non-root user, dropped capabilities, regular scanning.

**30. Why doesn't this repository wire a GitHub webhook to auto-trigger the Jenkins pipeline?**
An unreviewed push automatically rebuilding and redeploying to the whole Swarm cluster is a real production risk. The pipeline here is intentionally parameterized and manually triggered — a deliberate human gate before anything ships, not an oversight.

**31. Swarm vs. Kubernetes — when would you outgrow Swarm?**
Swarm has no built-in autoscaling (replica counts are set manually, not driven by metrics) and its load balancing is simple round-robin at the routing-mesh level. Once a workload needs metric-driven autoscaling, richer scheduling constraints, or a larger ecosystem of operators/controllers, teams typically move to Kubernetes — Swarm's advantage is being far simpler to stand up for small-to-mid clusters.
