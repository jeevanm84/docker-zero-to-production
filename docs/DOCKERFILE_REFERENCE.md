# Dockerfile reference and image internals

## Why a Dockerfile

Manually creating a container, installing software inside it, then running `docker commit` to snapshot it into a new image works — but it's manual, undocumented, and not repeatable (see the "manual image" anti-pattern below). A **Dockerfile** is a text file of instructions that Docker executes top-to-bottom to build an image automatically and consistently. `docker build` is the process that turns a Dockerfile into an image.

```
Dockerfile → docker build → Image → docker run → Container
```

### The anti-pattern this replaces

```bash
docker pull ubuntu
docker run -it --name ubuntucontainer ubuntu
# apt update -y && apt install apache2 python3 mysql-server -y   (manual, inside the container)
docker commit ubuntucontainer myimagewithapachenmysql
```

This works, but nobody can reproduce it from source, review it, or diff it. Every real project uses a Dockerfile instead.

## Instructions

| Instruction | Purpose | Runs at |
|---|---|---|
| `FROM` | Base image to build on top of | Build time |
| `RUN` | Execute a Linux command, result baked into the image | **Build** time |
| `CMD` | Default command/arguments for the container | **Container start**, easily overridden |
| `ENTRYPOINT` | The fixed, main executable of the container | Container start, not easily overridden |
| `COPY` | Copy local files into the image | Build time |
| `ADD` | Copy local files **or** a URL, and auto-extract local tar archives | Build time |
| `WORKDIR` | Set the default working directory | Build + runtime |
| `LABEL` | Attach metadata (author, version) to the image | Build time |
| `ENV` | Set an environment variable available in the built image and at runtime | Build + runtime |
| `ARG` | Build-time-only variable, not present in the running container by default | Build time only |
| `EXPOSE` | *Documents* the port the app listens on — does **not** publish it | Build time (documentation only) |
| `VOLUME` | Declare a mount point for persistent/shared data | Build + runtime |
| `STOPSIGNAL` | Which signal Docker sends on `docker stop` (default `SIGTERM`) | Runtime |
| `ONBUILD` | A trigger instruction that fires when *another* image uses this one as its `FROM` | Deferred to child build |

Instructions are conventionally written in capitals (`FROM`, not `from`) — this is a style convention, not a hard requirement, but every example in this repository follows it.

## RUN vs. CMD vs. ENTRYPOINT

This is the single most common Docker interview question, and the mental model is:

- `RUN` → executes **while the image is being built** and bakes its result into a layer. Use it to install packages, create files, compile things.
- `CMD` → the default command/arguments used **when the container starts**, and it is easily replaced by anything you put after the image name in `docker run`.
- `ENTRYPOINT` → the **fixed** main executable. Arguments after the image name in `docker run` are *appended* to it, not used to replace it (unless you pass `--entrypoint` explicitly).

### CMD alone — easily overridden

```dockerfile
FROM ubuntu:24.04
CMD ["echo", "Hello from CMD"]
```

```bash
docker run cmd-demo        # → Hello from CMD
docker run cmd-demo date   # → today's date; CMD was fully replaced
```

### ENTRYPOINT alone — arguments append, don't replace

```dockerfile
FROM ubuntu:24.04
ENTRYPOINT ["echo", "Hello from ENTRYPOINT"]
```

```bash
docker run entry-demo        # → Hello from ENTRYPOINT
docker run entry-demo date   # → Hello from ENTRYPOINT date  (date became an argument to echo)
```

### ENTRYPOINT + CMD together — the pattern used in real Dockerfiles

```dockerfile
FROM ubuntu:24.04
ENTRYPOINT ["echo"]
CMD ["Hello Docker"]
```

```bash
docker run both-demo                  # → Hello Docker
docker run both-demo "DNA by Reyaz"   # → DNA by Reyaz   (only CMD's default argument was replaced)
```

`ENTRYPOINT` stays fixed; `CMD` supplies (and lets you override) its default arguments. See the worked example with a real Python script in [`examples/dockerfiles/entrypoint-cmd-demo/`](../examples/dockerfiles/entrypoint-cmd-demo/).

If multiple `CMD` instructions exist in one Dockerfile, only the **last** one takes effect — the earlier ones are silently discarded.

## COPY vs. ADD

- `COPY` — copies local files/directories into the image. Simple, predictable. **Preferred for almost everything.**
- `ADD` — does what `COPY` does, plus: can fetch a remote URL directly, and auto-extracts local `.tar` archives into the destination. The extra magic (especially silent tar extraction) is exactly why `COPY` is recommended unless you specifically need one of `ADD`'s extra behaviors.

```dockerfile
FROM ubuntu
COPY index.html /tmp
ADD https://dlcdn.apache.org/tomcat/tomcat-10/v10.1.35/bin/apache-tomcat-10.1.35.tar.gz /tmp
```

## ENV vs. ARG

| | `ARG` | `ENV` |
|---|---|---|
| Scope | Build time only | Build time (after declared) **and** runtime |
| Set with | `docker build --build-arg VERSION=2.0` | `ENV key value` in the Dockerfile, or `docker run -e` |
| Visible in running container | No, not by default | Yes |

```dockerfile
ARG VERSION=1.0
FROM ubuntu
RUN echo $VERSION
```

## EXPOSE vs. `-p`

`EXPOSE 8080` in a Dockerfile is **documentation** — it tells a human (or `docker inspect`) that the app listens on 8080. It does **not** make the port reachable from the host. Only `docker run -p host:container` (or a Compose `ports:` entry) actually publishes a port.

## WORKDIR and LABEL

```dockerfile
FROM ubuntu
COPY index.html /tmp
WORKDIR /tmp
LABEL author Reyaz
```

`WORKDIR` changes the default directory a shell lands in inside the container (instead of `/`). `LABEL` attaches searchable metadata — view it with `docker inspect <container> | grep <label>`.

## A first real Dockerfile: serving a static site with Apache

```dockerfile
FROM ubuntu
RUN apt update
RUN apt install apache2 -y
RUN apt install apache2-utils -y
RUN apt clean
COPY website/ /var/www/html/
EXPOSE 80
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
```

`-D FOREGROUND` matters: Apache normally daemonizes (backgrounds itself). If it does that inside a container, the container's main process (PID 1) exits immediately, and **the container stops** — Docker only stays "running" while its main process is alive. `FOREGROUND` keeps Apache attached as PID 1, and its logs go to stdout/stderr where `docker logs` can see them. The full runnable version is in [`examples/dockerfiles/basic-apache-site/`](../examples/dockerfiles/basic-apache-site/).

## Image layers, caching, and the Union File System

Every `RUN`, `COPY`, and `ADD` instruction generally creates a new, read-only layer:

```
Layer 5   CMD
Layer 4   COPY index.html
Layer 3   RUN apt install nginx
Layer 2   RUN apt update
Layer 1   FROM ubuntu
```

The **Union File System (UnionFS)** merges all these read-only layers into a single filesystem view — the container doesn't see separate layers, it sees one coherent directory tree. When a container runs, Docker adds one **writable layer** on top; nothing below it ever changes. This is why deleting a container only removes that writable layer — the underlying image and its layers are untouched and stay on disk until you `docker rmi` them.

**Copy-on-write (CoW):** a file that exists in a lower, read-only layer is never duplicated until the container modifies it. On first write, Docker copies that file up into the writable layer and the modification happens there. Reads of unmodified files still come straight from the read-only layer below. This is what makes running 50 containers from the same base image cheap — they share every unmodified layer.

**Build caching:** Docker caches every successfully built layer and reuses it on the next build if that instruction and its inputs haven't changed. The moment one instruction's cache is invalidated, **every instruction after it** rebuilds too — order your Dockerfile so things that change rarely (installing dependencies) come before things that change often (copying application source):

```dockerfile
# Good: dependency layer stays cached across most rebuilds
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

```dockerfile
# Bad: any source change invalidates the pip install layer too
COPY . .
RUN pip install -r requirements.txt
```

`docker history <image>` shows every layer. `docker build --no-cache` forces a clean rebuild. `docker build --progress=plain .` gives verbose build logs.

## Image optimization checklist

1. **Use a smaller base image** — `alpine` or a `-slim` variant instead of a full `ubuntu`/`debian`.
2. **Combine `RUN` commands** — each `RUN` is a layer; fewer, larger layers build a smaller image:
   ```dockerfile
   # Bad — 3 layers
   RUN apt update
   RUN apt install nginx -y
   RUN apt install curl -y

   # Good — 1 layer, and cache cleaned up in the same layer it was created
   RUN apt update && \
       apt install -y nginx curl && \
       apt clean && \
       rm -rf /var/lib/apt/lists/*
   ```
3. **Use `.dockerignore`** — exclude `.git`, logs, `node_modules`, `target/`, etc. from the build context so they're never sent to the daemon or copied in.
4. **Prefer `COPY` over `ADD`** — predictable, no accidental extraction.
5. **Use multi-stage builds** — see below; keeps build tools out of the final image entirely.
6. **Pin versions, avoid `latest`** — `python:3.12-slim`, not `python:latest` — for reproducible builds.
7. **Clean package caches in the same `RUN`** that created them (cleaning in a later layer doesn't shrink the image — the earlier layer still has the cache in it).

## Multi-stage builds

A multi-stage build uses more than one `FROM` in a single Dockerfile. The first stage builds the application with full build tooling (Maven, npm); the final stage copies **only the built artifact** into a minimal runtime image. Everything from earlier stages — compilers, source, `node_modules`, the JDK used only to compile — is discarded and never ships.

```dockerfile
# ---------- Stage 1 : Build ----------
FROM maven:3.9.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

# ---------- Stage 2 : Runtime ----------
FROM tomcat:10.1-jdk17-temurin
RUN rm -rf /usr/local/tomcat/webapps/*
COPY --from=build /app/target/*.war /usr/local/tomcat/webapps/ROOT.war
EXPOSE 8080
CMD ["catalina.sh", "run"]
```

`COPY --from=build` pulls one file out of the named earlier stage without pulling in anything else from it. Runnable version: [`examples/dockerfiles/multi-stage-maven-tomcat/`](../examples/dockerfiles/multi-stage-maven-tomcat/). The same pattern applies to a Node.js frontend built and then served by nginx — see the worked example in that doc's "why this matters" section of [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).

**Advantages:** smaller image, faster pulls/deploys, smaller attack surface, no leaked build secrets or source, cleaner separation between "how it's built" and "how it runs."

## Base image, official image, custom image

| Type | Description | Example |
|---|---|---|
| Base image | The starting point named in `FROM` | `ubuntu:24.04`, `alpine:3.22` |
| Official image | Published/maintained upstream on Docker Hub | `nginx`, `mysql`, `python` |
| Custom image | Built by you for your application | `website:v1`, `mycompany/api:v2` |

## Distroless images

Distroless images (`gcr.io/distroless/*`, hosted on Google Container Registry, not Docker Hub) contain only an application's runtime dependencies — no shell, no package manager, no extra OS tooling. Smaller, fewer CVEs, and a much smaller attack surface, at the cost of harder debugging (no `docker exec ... /bin/sh` to poke around).

## `dockerfile.local`

Some teams keep a second `Dockerfile.local` (or `Dockerfile.dev`) specifically for local development — bind-mounting source directories, installing dev-only tooling, setting local environment variables — separate from the production `Dockerfile`, which stays optimized, minimal, and secure.

## Interview-ready answers

**What happens during `docker build`?** Docker reads the Dockerfile top to bottom, executes each instruction, creates a new image layer per instruction, reuses cached layers where the instruction and its inputs are unchanged, and produces the final image.

**Why should `COPY requirements.txt` come before `COPY . .`?** Application code changes far more often than its dependency list. Installing dependencies first lets Docker reuse that cached layer on almost every rebuild, so only the (fast) `COPY . .` layer and anything after it rebuild.

**What's the difference between an image and a container?** An image is a static, read-only blueprint. A container is a running (or stopped) instance created from that image, with its own writable layer on top.
