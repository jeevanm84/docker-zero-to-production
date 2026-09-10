# Lab 3 — Volumes and persistence

## Objective

Create and share all four storage types (named volume, anonymous volume, bind mount, tmpfs), confirm data survives a container being removed, and share one volume across multiple containers.

## Prerequisites

Labs 1–2 completed.

## Steps

### 1. Volume declared in a Dockerfile

```bash
cat > Dockerfile <<'EOF'
FROM ubuntu
VOLUME ["volume1"]
EOF
docker build -t reyaz:v1 .
docker run -it --name cont1 reyaz:v1
cd volume1 && touch file{1..5}
# Ctrl+P, Ctrl+Q
ls /var/lib/docker/volumes    # the volume's data on the Docker host

# find the actual volume mountpoint for cont1 and create files from the HOST side
MOUNT=$(docker inspect cont1 --format '{{ (index .Mounts 0).Source }}')
sudo touch "$MOUNT"/python{1..5}

docker attach cont1
cd volume1 && ls               # host-created files are visible here too — bidirectional
```

### 2. Share a volume between containers with `--volumes-from`

```bash
docker run -it --name cont2 --volumes-from cont1 ubuntu
ls; cd volume1; ls              # same data as cont1
```

### 3. Volume from `docker run -v`

```bash
docker run -it --name cont4 -v /volume2 ubuntu
cd volume2/ && touch python{1..5}
# Ctrl+P, Ctrl+Q
docker run -it --name cont5 --volumes-from cont4 ubuntu
cd volume2 && touch python{6..10}   # visible back on cont4 too
```

### 4. Named volume with `--mount`

```bash
docker volume create volume3
docker volume inspect volume3
sudo touch /var/lib/docker/volumes/volume3/_data/html{1..5}
docker run -it --name cont6 --mount source=volume3,destination=/volume3 ubuntu
cd /volume3 && ls               # host-created files are already here
```

### 5. Bind mount

```bash
mkdir ~/website
echo "Hello Docker" > ~/website/index.html
docker run -d -p 80:80 -v ~/website:/usr/share/nginx/html nginx
curl http://localhost
echo "Hello Mr Docker" > ~/website/index.html
curl http://localhost           # changed instantly, no rebuild
```

### 6. tmpfs mount

```bash
docker run -d --tmpfs /app/cache --name tmpfstest nginx
docker exec tmpfstest sh -c "echo test > /app/cache/f.txt && cat /app/cache/f.txt"
docker restart tmpfstest
docker exec tmpfstest ls /app/cache   # empty — tmpfs data is gone after a restart
```

## Expected observations

- Data in `volume1`/`volume2`/`volume3` on the host and inside the container stays in sync in both directions.
- Removing a container that used a named volume does **not** delete the volume's data — only `docker volume rm` does.
- tmpfs data does not survive a container restart.

## Verification

```bash
docker volume ls
docker volume inspect volume3
docker inspect cont6 | grep -A5 Mounts
```

## Cleanup

```bash
docker kill $(docker ps -aq); docker rm $(docker ps -aq)
docker volume rm volume3
docker rmi -f $(docker images -q)
```

## Extension exercise

Attach a real block device (an AWS EBS volume, or a second local disk) as a bind mount, following the steps in `docs/STORAGE_AND_NETWORKING.md` under "Attaching a real AWS EBS volume," and confirm the same bidirectional behavior holds for real persistent block storage.
