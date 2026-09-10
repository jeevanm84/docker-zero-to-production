# Architecture

## Physical, VM, and container — what actually changes

| | Physical server | Virtual machine | Container |
|---|---|---|---|
| What you get | Dedicated hardware | Emulated hardware + own OS kernel | A packaged process sharing the host kernel |
| Boot time | Minutes | Tens of seconds to minutes | Milliseconds to seconds |
| Isolation unit | The whole machine | Hypervisor (ESXi, KVM, Hyper-V) | Linux namespaces + cgroups |
| "Image" equivalent | — | An AMI / VM template | A container image |
| Overhead | None (but wasted capacity) | A full guest OS per VM | Just the app + its dependencies |
| Cost | Highest | Medium | Lowest (most density per host) |

A container is not a lightweight VM. It has no kernel of its own — every container on a host shares that host's Linux kernel. What looks like "the OS" inside a container (Ubuntu, Alpine, Amazon Linux userland) is just a filesystem image providing libraries and tools; there is no second kernel booting underneath it. This is exactly why containers start in milliseconds and VMs don't.

## Why this matters: the dependency problem

Before containerization, an application's dependencies (a specific Java version for Jenkins, Python for the AWS CLI, a matching Tomcat version) had to be installed and kept consistent on every machine that ran it — dev laptop, CI runner, and every environment in between. Any drift between those installations ("works on my machine") caused failures that had nothing to do with the application code.

Containerization packages the application **and** its exact dependency set into one artifact — the image — so the same bundle runs identically everywhere the container runtime runs. This is OS-level virtualization: one kernel, many isolated user-space environments.

## Monolithic vs. microservices (the business framing)

Take Amazon's consumer platform: Amazon Fresh, Prime Video, AWS, and retail are conceptually independent services with different scaling needs, release cadences, and failure domains, but they're offered under one brand. Or take a bank like HDFC: internet banking, mobile banking, insurance, and loans are separable business capabilities.

- **Monolithic**: all of that ships as one deployable unit. One bug in loans can take down internet banking. Scaling means scaling the whole thing, even if only one module is under load.
- **Microservices**: each capability is its own service, independently deployable, independently scalable, with its own failure blast radius. This repository's HDFC-style lab (`labs/05-compose-multi-service-bank-app.md`) builds exactly this: `internetbanking`, `mobilebanking`, `insurance`, and `loan` as four separate containers behind four separate ports, each built from its own Dockerfile and image.

Containers are the natural deployment unit for microservices: one container per service, versioned and shipped independently.

## Docker's request path

See [`diagrams/docker-architecture.svg`](../diagrams/docker-architecture.svg) for the full picture. In short:

```
docker run nginx
       │
       ▼
Docker Client (CLI) ──REST API──▶ Docker Daemon (dockerd)
                                        │
                         ┌──────────────┼───────────────┐
                         ▼              ▼                ▼
                     Images        Containers    Networks / Volumes
                         │
                         ▼
                    containerd  (manages container lifecycle: pull, storage, lifecycle events)
                         │
                         ▼
                       runc     (OCI runtime: actually creates the container process)
                         │
                         ▼
                   Linux Kernel (namespaces + cgroups)
                         │
                         ▼
                 Running container process
```

- **Docker Client** — where you type commands. It does not create anything itself; it sends a request over the REST API to the daemon.
- **Docker Daemon (`dockerd`)** — the brain. Pulls/builds images, runs/stops containers, creates networks and volumes.
- **Docker Host** — the machine running the daemon: an EC2 instance, a laptop, a VM.
- **Docker Registry** — stores and serves image layers (Docker Hub, ECR, GHCR, a private registry).
- **containerd** — the container lifecycle manager sitting between the daemon and the low-level runtime.
- **runc** — the actual OCI-compliant runtime that talks to the kernel to create the isolated process.

### Flow when you run `docker run <image>`

1. Client sends the request to the daemon.
2. Daemon checks whether the image exists locally.
3. If not, it pulls the image from the configured registry (default: Docker Hub).
4. Daemon creates the container: sets up namespaces and cgroups, attaches networking, adds the writable layer.
5. `containerd` → `runc` start the actual container process.
6. The process defined by `ENTRYPOINT`/`CMD` runs, and the container is now "running."

## Isolation and resource management

Containers are not VMs — isolation and limits both come from the Linux kernel, not from a hypervisor:

- **Namespaces** provide isolation so a container can't see another container's resources:
  - `PID` — process isolation (a container's PID 1 is not the host's PID 1)
  - `NET` — network isolation (its own interfaces, routes, ports)
  - `MNT` — filesystem isolation (its own mount point view)
- **cgroups (control groups)** enforce resource *limits* — CPU, memory, I/O — so one container cannot starve the others or the host.

## Docker editions

| | Community Edition (CE) | Enterprise Edition (EE) |
|---|---|---|
| Cost | Free | Commercial |
| Includes | Docker Engine, CLI, Compose, Build | Everything in CE, plus: |
| Extra | — | Advanced security, image scanning, RBAC, compliance features, certified plugins, SLA support |

Docker CE is what every lab in this repository uses.

## Container lifecycle

```
Created → Running → Paused → Stopped → Removed
             ▲                   │
             └────── Restarted ──┘
```

`docker create` makes a container without starting it. `docker run` = `create` + `start`. `docker pause`/`unpause` freezes/resumes processes without stopping the container. `docker stop` sends `SIGTERM` (graceful) and waits; `docker kill` sends `SIGKILL` (immediate, no grace period).

## OCI (Open Container Initiative)

Launched in 2015 under the Linux Foundation (Docker, Red Hat, Google, and others as contributors) to stop every vendor from inventing its own incompatible image/runtime format. OCI defines two specifications:

- **Image Specification** — standard image format: layers, manifest.
- **Runtime Specification** — how a container is created and run: process execution, filesystem layout, namespace/cgroup usage.

Because Docker images follow the OCI Image Specification, the same image runs on any OCI-compliant runtime — `containerd`, `CRI-O`, `Podman` — not just Docker. That portability is the entire point of the standard.

## Docker vs. its alternatives

Docker is free, open source, written in Go, introduced in 2013, and configured largely through YAML (Compose). It's the dominant tool but not the only one: **Podman**, **containerd** (standalone), **CRI-O**, and **rkt (Rocket, deprecated)** are alternatives that speak the same OCI formats.
