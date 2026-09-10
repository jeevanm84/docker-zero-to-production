# Lab 4 — Networking

## Objective

Compare the default bridge network to a user-defined bridge, confirm container-to-container name resolution only works on the latter, and try the host and none drivers.

## Prerequisites

Labs 1–3 completed.

## Steps

### 1. Inspect the default network

```bash
docker network ls
docker run -itd --name cont1 -p 81:80 nginx:latest
docker run -itd --name cont2 -p 82:80 nginx:latest
docker inspect cont1 | grep -A5 NetworkSettings
docker inspect cont2 | grep -A5 NetworkSettings
```

### 2. Try to ping by name on the default bridge (expected to fail without extra config)

```bash
docker exec -it cont2 /bin/bash
apt update && apt install iputils-ping -y
ping cont1     # fails — default bridge has no built-in DNS by container name
exit
```

### 3. Create a user-defined bridge and connect both containers

```bash
docker network create reyaz
docker network connect reyaz cont1
docker network connect reyaz cont2
docker network inspect reyaz    # both containers now listed
docker exec -it cont2 /bin/bash
ping cont1     # now resolves and works — user-defined bridges provide DNS by name
exit
```

### 4. Disconnect and clean up the network

```bash
docker network disconnect reyaz cont2
docker network inspect reyaz    # cont2 no longer listed
docker network prune
docker network rm reyaz
```

### 5. Host network

```bash
docker run -d --network host --name hostnet nginx
curl http://localhost:80        # reaches nginx directly, no -p mapping needed
docker rm -f hostnet
```

### 6. None network

```bash
docker run -it --network none --name isolated ubuntu
# inside: try any network call — only localhost is reachable
curl http://example.com || echo "no network, as expected"
exit
```

## Expected observations

- Two containers on the default bridge can reach each other by IP, not by name.
- A user-defined bridge adds DNS resolution by container name — this is exactly why Compose always creates one automatically for you.
- `--network host` skips NAT/port mapping entirely; `--network none` disables networking except loopback.

## Verification

```bash
docker network ls
docker network inspect bridge
```

## Cleanup

```bash
docker kill $(docker ps -aq); docker rm $(docker ps -aq)
docker network prune -f
```

## Extension exercise

Create a `macvlan` network (requires a host NIC that supports promiscuous mode) and confirm the container gets its own MAC/IP visible to other devices on the physical LAN — compare `docker inspect` output for a macvlan container against a bridge container.
