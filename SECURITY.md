# Security policy

This repository contains educational documentation, Dockerfiles, and Compose examples — it does not run a live service. For the security *practices* covered by this repository's content (non-root users, capability drops, image scanning, secrets), see [`docs/SECURITY.md`](docs/SECURITY.md).

## Reporting a vulnerability

If you find a security issue in this repository itself — for example, an example Dockerfile that would encourage an insecure default, or a script that mishandles input — please use GitHub's private vulnerability reporting for this repository rather than opening a public issue.

## Scope

- In scope: the example Dockerfiles, Compose/stack files, the Jenkins pipeline example, and the validation script.
- Out of scope: vulnerabilities in Docker Engine, Docker Hub, or upstream base images themselves — report those to the [Docker Security team](https://www.docker.com/trust/security/) or the relevant image maintainer.
