# Code structure

What lives where and why.

```
docker-zero-to-production/
├── README.md                     — entry point, learning path, repository map
├── diagrams/
│   └── docker-architecture.svg   — client → daemon → containerd → runc → kernel, plus Swarm cluster
├── docs/
│   ├── ARCHITECTURE.md           — physical/VM/container, monolith vs. microservices, Docker's request path, OCI
│   ├── DOCKERFILE_REFERENCE.md   — every Dockerfile instruction, RUN/CMD/ENTRYPOINT, layers, caching, multi-stage builds
│   ├── STORAGE_AND_NETWORKING.md — volumes (named/anonymous/bind/tmpfs), the 5 network drivers, resource limits
│   ├── COMPOSE_AND_SWARM.md      — Compose YAML, Swarm cluster ops, services, secrets, replicated vs. global
│   ├── SECURITY.md               — least privilege, non-root, capabilities, image scanning, secrets
│   ├── CI_CD_PIPELINE.md         — the Jenkins parameterized build → tag → push → Swarm deploy pipeline
│   ├── TROUBLESHOOTING.md        — 10 incident-style scenarios: symptom → root cause → fix → why
│   ├── INTERVIEW_QUESTIONS.md    — fundamentals through architect/SRE level
│   ├── END_TO_END_GUIDE.md       — one guided path through every tier and lab
│   └── ROADMAP.md                — where this fits in the wider jeevanm84 portfolio
├── labs/                         — hands-on, numbered, run-it-yourself labs (see below)
├── examples/
│   ├── dockerfiles/              — one concept per directory, each independently buildable
│   ├── compose/                  — three runnable multi-service Compose stacks
│   └── jenkins/                  — the Jenkinsfile and stack file referenced by CI_CD_PIPELINE.md
├── scripts/check.py              — Markdown link/structure and identity validation, run in CI
└── .github/                      — CI workflow, issue templates, PR template, CODEOWNERS
```

## Labs, in order

| Lab | Topic | Requires |
|---|---|---|
| `01-container-fundamentals.md` | Pull, run, exec/attach, lifecycle, cleanup | Docker only |
| `02-dockerfile-build-and-optimize.md` | Build a Dockerfile, inspect layers, apply the optimization checklist | Docker only |
| `03-volumes-and-persistence.md` | All four storage types, share a volume across containers | Docker only |
| `04-networking.md` | Bridge vs. user-defined bridge, container-to-container DNS | Docker only |
| `05-compose-multi-service-bank-app.md` | Four-module HDFC-style app behind Compose | Docker + Compose |
| `06-swarm-ha-cluster.md` | 3-node Swarm cluster, services, scaling, self-healing, rollback | 3 hosts/VMs |
| `07-jenkins-image-pipeline.md` | Parameterized Jenkins pipeline: build → tag → push → `docker stack deploy` | Swarm cluster + Jenkins |

## `examples/dockerfiles/` — one idea per directory

- `basic-apache-site/` — the minimal "serve a static site" Dockerfile, including the `-D FOREGROUND` fix for the "container exits immediately" failure mode.
- `entrypoint-cmd-demo/` — a tiny Python script proving the CMD-gets-replaced vs. ENTRYPOINT-gets-appended-to behavior from `docs/DOCKERFILE_REFERENCE.md`.
- `flask-app/` — a minimal Flask app with a properly layered Dockerfile (`requirements.txt` copied and installed before the rest of the source).
- `multi-stage-maven-tomcat/` — a two-stage build: Maven compiles a WAR, Tomcat serves it; the JDK/Maven toolchain never reaches the final image.
- `nginx-load-balancer/` — an Nginx image built from a custom `nginx.conf` implementing a reverse-proxy load balancer across backend containers.

## `examples/compose/`

- `hdfc-bank-modules/` — the four-service banking example (`internetbanking`, `mobilebanking`, `insurance`, `loan`) as one `docker-compose.yml`.
- `flask-nginx-lb/` — three replicas of the Flask app from `examples/dockerfiles/flask-app/`, load-balanced by Nginx, with `nginx.conf` bind-mounted in.
- `swarm-stack-with-secrets/` — Postgres + Adminer, with the database password delivered as a Docker secret rather than a plaintext environment variable — deployed with `docker stack deploy`, not `docker compose up`.

## `examples/jenkins/`

- `Jenkinsfile` — the parameterized `checkout → build → tag → push → deploy` pipeline described in `docs/CI_CD_PIPELINE.md`.
- `docker-compose.yml` — the Swarm stack file the pipeline's `deploy` stage targets (3 replicas per module).
