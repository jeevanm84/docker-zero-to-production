# A Jenkins + Docker + Swarm image pipeline

This is the end-to-end project this repository builds toward: a **parameterized** Jenkins pipeline that builds one of several application images from a shared Dockerfile-per-module repo, tags it, pushes it to Docker Hub, and deploys the whole multi-service stack to a Docker Swarm cluster — matching the HDFC-bank-style `internetbanking` / `mobilebanking` / `insurance` / `loan` modules used throughout this repository.

Full runnable files: [`examples/jenkins/`](../examples/jenkins/). Step-by-step build instructions: [`labs/07-jenkins-image-pipeline.md`](../labs/07-jenkins-image-pipeline.md).

## Topology

```
Manager node  (t2.medium) — Jenkins + Docker Swarm manager
Worker node 1 (t2.micro)  — Swarm worker
Worker node 2 (t2.micro)  — Swarm worker
```

Jenkins runs **on the Swarm manager**, and its pipeline shells out to the `docker` CLI on that same host — which is why the Jenkins container/process needs access to `/var/run/docker.sock` (see the permissions note below).

## Why parameters, not one Dockerfile per pipeline

There isn't one image to build — there are four (`internetbanking`, `mobilebanking`, `insurance`, `loan`), all structurally identical, differing only in `index.html` and the target image/tag. Rather than four near-duplicate pipelines, the image name and the destination Docker Hub repo are **build parameters**, and the pipeline stages use `$image` / `$repo` instead of a hardcoded value:

- Parameter `image` (choice): `internetbanking:v1`, `mobilebanking:v1`, `insurance:v1`, `loans:v1`
- Parameter `repo` (choice): `trainerreyaz/ib-image`, `trainerreyaz/mb-image`, `trainerreyaz/insurance-image`, `trainerreyaz/loans-image`

## Pipeline stages

```groovy
pipeline {
    agent any
    stages {
        stage('checkout') {
            steps { git 'https://github.com/<you>/dockerproject.git' }
        }
        stage('build') {
            steps { sh 'docker build -t $image .' }
        }
        stage('tag') {
            steps { sh 'docker tag $image $repo' }
        }
        stage('push') {
            steps {
                sh 'docker login -u <dockerhub-username> -p $password'
                sh 'docker push $repo'
            }
        }
        stage('deploy') {
            steps { sh 'docker stack deploy bank -c docker-compose.yml' }
        }
    }
}
```

- `$password` is injected as a Jenkins environment variable (**Manage Jenkins → System → Environment variables**), never typed into the pipeline script itself — see `docs/SECURITY.md` for why secrets never belong in source-controlled files.
- `deploy` uses `docker stack deploy`, not `docker-compose up` — the target is the whole Swarm cluster, not just the Jenkins host, so the multi-service application ends up running with replicas spread across the manager and both workers.

## Letting Jenkins run Docker commands

Jenkins needs permission to reach the Docker socket on its host:

```bash
chmod 777 /var/run/docker.sock
systemctl daemon-reload
systemctl restart docker.service
```

`chmod 777` on the socket is the quick path used for a training/lab environment. In anything production-facing, prefer adding the Jenkins user to the `docker` group (`usermod -aG docker jenkins`) instead of world-writable permissions on the socket — see `docs/SECURITY.md` for the least-privilege rationale this trades against.

## The deploy target: `docker-compose.yml` for `docker stack deploy`

```yaml
version: '3.8'
services:
  internetbanking:
    image: trainerreyaz/ib-image:latest
    ports:
      - "81:80"
    deploy:
      replicas: 3
    volumes:
      - /var/lib/internetbanking
  mobilebanking:
    image: trainerreyaz/mb-image:latest
    ports:
      - "82:80"
    deploy:
      replicas: 3
    volumes:
      - /var/lib/mobilebanking
  insurance:
    image: trainerreyaz/insurance-image:latest
    ports:
      - "83:80"
    deploy:
      replicas: 3
    volumes:
      - /var/lib/insurance
  loan:
    image: trainerreyaz/loans-image:latest
    ports:
      - "84:80"
    deploy:
      replicas: 3
    volumes:
      - /var/lib/loan
```

Each module gets 3 replicas distributed across the cluster, so the module's routing-mesh port stays reachable even if one node goes down.

## Operating the deployed stack

```bash
docker stack ls
docker stack services bank
docker stack ps bank
docker service ls
docker service rm <service-name>   # or: docker stack rm bank
```

## Why this repository does *not* wire a webhook

A GitHub push webhook auto-triggering this pipeline is deliberately **not** part of this design: an automatic build-and-deploy-to-production on every push, with no human gate, is a real production risk (a bad push reaches the whole cluster with nobody reviewing it first). This pipeline is triggered manually with an explicit `image`/`repo` selection — a conscious gate before anything ships. See `CONTRIBUTING.md` for how this repository scopes CI (validation only, no auto-deploy) for the same reason.

## Also useful: a standalone MySQL container for local testing

Not part of the Jenkins pipeline, but a common companion when testing one of these services against a real database locally:

```bash
docker run -d --name mysql-db \
  -e MYSQL_ROOT_PASSWORD=my-secret-pw \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=myuser \
  -e MYSQL_PASSWORD=mypassword \
  -p 3306:3306 \
  -v mysql_data:/var/lib/mysql \
  --restart unless-stopped \
  mysql:latest
```

Note the plaintext password on the command line here — acceptable for a disposable local lab container, not for anything shared or production-facing (use a Docker/Swarm secret instead, per `docs/SECURITY.md`).
