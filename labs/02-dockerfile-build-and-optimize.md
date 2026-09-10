# Lab 2 — Dockerfile build and optimization

## Objective

Write and build Dockerfiles that exercise `RUN`, `CMD`, `ENTRYPOINT`, `COPY`, `ADD`, `WORKDIR`, `LABEL`, `ENV`, `ARG`, and `EXPOSE`; inspect layers; then apply the image-optimization checklist and measure the difference.

## Prerequisites

Lab 1 completed. A Linux host with Docker.

## Steps

### 1. `RUN` — baked in at build time

```bash
mkdir ~/dockerlab && cd ~/dockerlab
cat > Dockerfile <<'EOF'
FROM ubuntu
RUN apt update -y
RUN apt install git maven tree apache2 -y
RUN touch file1
EOF
docker build -t reyaz:v1 .
docker run -it --name cont1 reyaz:v1
# check installed versions, then Ctrl+P, Ctrl+Q
```

### 2. `CMD` — only runs after the container starts

```bash
cat > Dockerfile <<'EOF'
FROM ubuntu
RUN apt update -y
RUN apt install git maven tree apache2 -y
RUN touch file1
RUN apt install python3 -y
CMD apt install mysql-server -y
EOF
docker build -t reyaz:v2 .
docker run -it --name cont2 reyaz:v2
# watch mysql-server install now — CMD runs post-container-creation, not at build time
```

### 3. `COPY` vs `ADD`

```bash
touch index.html
cat > Dockerfile <<'EOF'
FROM ubuntu
COPY index.html /tmp
ADD https://dlcdn.apache.org/tomcat/tomcat-10/v10.1.35/bin/apache-tomcat-10.1.35.tar.gz /tmp
EOF
docker build -t reyaz:v3 .
docker run -it --name cont3 reyaz:v3
cd /tmp && ls   # the .tar.gz was fetched AND extracted automatically by ADD
```

### 4. `WORKDIR` and `LABEL`

```bash
cat >> Dockerfile <<'EOF'
WORKDIR /tmp
LABEL author Reyaz
EOF
docker build -t reyaz:v4 .
docker run -it --name cont4 reyaz:v4
# default path is now /tmp
docker inspect cont4 | grep -i Reyaz
```

### 5. `ENV` and `EXPOSE`

```bash
cat > Dockerfile <<'EOF'
FROM ubuntu
ENV course devops
ENV trainer Reyaz
EXPOSE 8080
EOF
docker build -t reyaz:v5 .
docker run -it --name cont5 reyaz:v5
echo $course
echo $trainer
# Ctrl+P, Ctrl+Q, then:
docker ps -a   # port 8080 appears in the PORTS column (documented, not published)
```

### 6. Build the full static-site image

Use [`examples/dockerfiles/basic-apache-site/`](../examples/dockerfiles/basic-apache-site/):

```bash
cd examples/dockerfiles/basic-apache-site
docker build -t firstproject:v1 .
docker run -itd --name webcont1 -p 80:80 firstproject:v1
curl http://localhost
```

### 7. Inspect layers and caching

```bash
docker history firstproject:v1
docker build --no-cache -t firstproject:v1 .
docker build --progress=plain -t firstproject:v1 .
```

### 8. Multi-stage build

Build [`examples/dockerfiles/multi-stage-maven-tomcat/`](../examples/dockerfiles/multi-stage-maven-tomcat/) and compare its final image size against a single-stage equivalent that keeps Maven installed:

```bash
cd ../multi-stage-maven-tomcat
docker build -t my-web-app .
docker images my-web-app
docker run -d -p 8080:8080 my-web-app
```

## Expected observations

- `RUN` executes during `docker build`; `CMD` only executes once the container starts.
- `docker history` shows one layer per `RUN`/`COPY`/`ADD` instruction.
- The multi-stage image is dramatically smaller than a single-stage build that keeps the JDK/Maven toolchain installed.

## Verification

```bash
docker images | grep -E 'reyaz|firstproject|my-web-app'
docker inspect cont4 --format '{{.Config.WorkingDir}}'   # should print /tmp
```

## Cleanup

```bash
docker kill $(docker ps -aq); docker rm $(docker ps -aq)
docker rmi -f $(docker images -q)
```

## Extension exercise

Take the `basic-apache-site` Dockerfile and apply the optimization checklist from `docs/DOCKERFILE_REFERENCE.md`: combine the three `apt` `RUN` lines into one with cache cleanup, switch to a smaller base if possible, and add a `.dockerignore`. Rebuild and compare `docker images` size before and after.
