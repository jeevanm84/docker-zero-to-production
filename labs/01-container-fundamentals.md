# Lab 1 — Container fundamentals

## Objective

Pull images, create and run containers three different ways (interactive, detached, exec), understand the difference between `attach` and `exec`, and clean up completely.

## Prerequisites

A single Linux host with Docker installed (Amazon Linux 2023 EC2 instance, or Docker Desktop locally).

```bash
sudo yum install docker -y      # Amazon Linux
sudo systemctl start docker
sudo systemctl status docker
docker -v
```

## Steps

### 1. Pull two base images

```bash
docker images
docker pull amazonlinux
docker pull ubuntu
docker images
```

### 2. Interactive container (`-it`) — logs you straight in

```bash
docker run -it --name amazonlinuxcontainer amazonlinux
# now inside the container:
ls
yum install git maven tree httpd -y
touch file{1..10}
# detach WITHOUT stopping it:
```
Press `Ctrl+P` then `Ctrl+Q` to detach.

### 3. Detached container (`-d`) — doesn't log you in

```bash
docker run -it -d --name ubuntucontainer ubuntu
docker ps -a
docker ps
```

### 4. `attach` vs. `exec`

```bash
docker attach ubuntucontainer
apt update
apt install nginx -y
```
Detach with `Ctrl+P, Ctrl+Q` again — **do not** type `exit` here, or the container stops (see `docs/TROUBLESHOOTING.md` #2).

```bash
docker exec -it ubuntucontainer /bin/bash
apt update -y
apt install git -y
apt install apache2 -y
service apache2 start
service apache2 status
exit
docker ps -a    # container is still running — exec started a separate process
```

## Expected observations

- `docker attach` connects to the container's main process (PID 1); `exit` there stops the container.
- `docker exec` starts an independent process; `exit` there leaves the container running.
- `docker ps -a` lists all containers regardless of state; `docker ps` lists only running ones.

## Verification

```bash
docker ps -a
docker inspect ubuntucontainer | grep -i status
```

## Useful commands to practice

```bash
docker search ubuntu
docker stop <container>       # graceful (SIGTERM, waits)
docker start <container>
docker restart <container>
docker pause <container>
docker unpause <container>
docker inspect <container>
docker kill <container>       # immediate (SIGKILL, no grace period)
docker logs <container>
docker top <container>
docker stats <container>
docker diff <container>
docker cp hello.txt <container>:/tmp
docker save ubuntu > ubuntu.tar
docker load -i ubuntu.tar
docker history <image>
docker image prune
```

## Cleanup

```bash
docker kill $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi -f $(docker images -q)
docker ps -a
docker images
```

## Extension exercise

Create a custom image from a manually-configured container using `docker commit` (`docker commit ubuntucontainer myimagewithapachenmysql`), then run a new container from it. Notice this works but isn't reproducible from source — that gap is exactly what Lab 2's Dockerfile approach fixes.
