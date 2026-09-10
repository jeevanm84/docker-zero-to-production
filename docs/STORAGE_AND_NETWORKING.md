# Storage and networking

## Volumes — why they exist

A container's writable layer is deleted with the container. Anything the application needs to survive a `docker rm` — a database's data directory, uploaded files, a Jenkins home — has to live outside that writable layer, on storage that outlives the container. That's a **volume**: a folder that Docker manages, stored on the host filesystem, independent of any single container's lifecycle.

- A volume can be shared across multiple containers at once.
- It's bidirectional: a file created inside the container appears on the host, and vice versa.
- Data lives under `/var/lib/docker/volumes/` on the Docker host by default.
- Containers otherwise use the host's CPU/RAM directly — volumes are specifically about *persistent storage*, not compute.

### Four storage options

| Type | Named by you? | Typical use |
|---|---|---|
| **Named volume** | Yes | Databases, app state — the default recommended choice |
| **Anonymous volume** | No (random ID) | Created implicitly by `VOLUME` in a Dockerfile; hard to reuse deliberately |
| **Bind mount** | N/A — maps a specific host path | Local development, live-editing config/source |
| **tmpfs mount** | N/A — RAM only | Caches/secrets that must never touch disk |

### Method 1 — declared in a Dockerfile

```dockerfile
FROM ubuntu
VOLUME ["volume1"]
```

Files written under `volume1` inside the container are mirrored to `/var/lib/docker/volumes/...` on the host, and vice versa.

### Method 2 — created with `docker run -v`

```bash
docker run -it --name cont4 -v /volume2 ubuntu
```

### Sharing a volume between containers — `--volumes-from`

```bash
docker run -it --name cont1 -v /volume1 ubuntu
docker run -it --name cont2 --volumes-from cont1 ubuntu   # cont2 now sees cont1's volume1
docker run -it --name cont3 --volumes-from cont2 ubuntu   # chains further
```

### Method 3 — named volumes with `docker volume` + `--mount`

```bash
docker volume create volume3
docker volume inspect volume3
docker run -it --name cont6 --mount source=volume3,destination=/volume3 ubuntu
```

`--mount` is the more explicit, recommended syntax over `-v` for anything beyond quick testing — it separates `source`/`destination`/options clearly instead of packing them into one string.

### Bind mounts — map a host directory straight in

```bash
mkdir website
echo "Hello Docker" > website/index.html
docker run -d -p 80:80 -v $(pwd)/website:/usr/share/nginx/html nginx
```

Edit `website/index.html` on the host and refresh the browser — the change is live immediately, no rebuild. This is why bind mounts are the standard pattern for local development, but a poor fit for production images (the image should be self-contained, not depend on a host path existing).

### tmpfs mounts — RAM only, nothing on disk

```bash
docker run -d --tmpfs /app/cache nginx
```

Extremely fast, but data disappears the moment the container stops. Use for caches, session state, or secrets you explicitly do not want persisted to disk.

### Attaching a real AWS EBS volume

```bash
lsblk
sudo mkfs -t ext4 /dev/nvme1n1
sudo mkdir /mnt/ebs-volume
sudo mount /dev/nvme1n1 /mnt/ebs-volume
docker run -it --name my-container1 -v /mnt/ebs-volume:/mynewebsvolume ubuntu
```

This is a bind mount under the hood — the EBS volume is just a formatted, mounted block device on the host, and Docker is bind-mounting a path on it.

## Docker networking

Docker networking lets containers on the same host, or across different hosts, talk to each other. There are five network drivers:

| Driver | Scope | Use case |
|---|---|---|
| **bridge** | Same host | Default network; each container gets a private IP (`docker0`, `172.17.0.0/16` by default) |
| **overlay** | Multiple hosts | Containers on different Docker hosts communicate as if on one network — the backbone of Swarm services |
| **host** | Same host, no isolation | Container shares the host's network stack directly: no NAT, no port mapping, highest performance, but port conflicts and reduced isolation |
| **none** | Fully isolated | No networking at all — only `localhost`; for security testing, offline batch processing, sensitive workloads |
| **macvlan** | Physical LAN | Each container gets its own MAC and IP on the physical network, appearing as a separate device — for legacy apps, DHCP-based environments, network appliances |

```
                    Host Machine

             +----------------------+
             |     docker0 Bridge   |
             +----------+-----------+
                        |
        -------------------------------
        |             |              |
        ▼             ▼              ▼
   Container1    Container2    Container3
   172.17.0.2    172.17.0.3    172.17.0.4
```

### Default bridge vs. a user-defined bridge

The **default bridge** network lets containers reach each other only by IP unless you do extra configuration. A **user-defined bridge** (`docker network create mynet`) gives you built-in DNS: containers on it can resolve each other **by container name**, which is why Compose (and every real multi-container setup) always creates its own user-defined network rather than relying on the default.

```bash
docker network create reyaz
docker run -itd --name cont1 -p 81:80 nginx:latest
docker run -itd --name cont2 -p 82:80 nginx:latest
docker network connect reyaz cont1
docker network connect reyaz cont2
docker network inspect reyaz          # shows both containers on the same network
docker exec -it cont2 /bin/bash
#   ping <cont1's IP>                 # works — cont1 and cont2 are on a shared network now
docker network disconnect reyaz cont2
docker network rm reyaz
```

`docker network prune` removes unused networks; `docker system prune` also cleans up networks (plus stopped containers, dangling images, and build cache).

## Resource management

By default a container has **no limits** — it can consume as much CPU/RAM as the host has. Always cap resources in anything resembling production:

```bash
docker run -it --name cont7 --cpus="0.1" --memory="300mb" ubuntu
docker update cont7 --cpus="0.7" --memory="300mb"    # change limits on a running container
docker stats                                          # live CPU/memory usage per container
```

Resource limits can never exceed what the Docker host itself has available.

## Interview-ready answers

**Named volume vs. bind mount?** Named volume: Docker-managed, lives under `/var/lib/docker/volumes/`, best for persistent application data like databases. Bind mount: maps a specific host path in directly, best for local development and live config/source editing.

**What is tmpfs?** A mount backed by host RAM instead of disk. Data is lost when the container stops — ideal for caches or sensitive data that should never be written to disk.

**When would you use the host network?** When you need maximum network performance and can accept reduced isolation and no port remapping — for example, a monitoring agent or a high-throughput network service.

**What's an overlay network for?** Connecting containers across multiple Docker hosts as if they were on one network — it's what makes Swarm services reachable from any node in the cluster.
