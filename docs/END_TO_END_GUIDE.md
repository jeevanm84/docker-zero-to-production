# End-to-end guide

One continuous path through every tier. Each step links to the doc or lab that covers it in full.

## Tier 1 — Beginner (no cloud account, no cost)

1. Read [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — physical vs. VM vs. container, why containerization solves the dependency problem, Docker's internal request path.
2. Study [`diagrams/docker-architecture.svg`](../diagrams/docker-architecture.svg) until you can redraw the client → daemon → containerd → runc → kernel chain from memory.
3. Read [`docs/DOCKERFILE_REFERENCE.md`](DOCKERFILE_REFERENCE.md) alongside [`examples/dockerfiles/basic-apache-site/Dockerfile`](../examples/dockerfiles/basic-apache-site/Dockerfile) and [`examples/dockerfiles/entrypoint-cmd-demo/`](../examples/dockerfiles/entrypoint-cmd-demo/).
4. Do [`labs/01-container-fundamentals.md`](../labs/01-container-fundamentals.md) and [`labs/02-dockerfile-build-and-optimize.md`](../labs/02-dockerfile-build-and-optimize.md) — both run entirely on a single Docker host (a free-tier EC2 instance, or Docker Desktop locally).
5. Answer the Fundamentals and Dockerfile sections of [`docs/INTERVIEW_QUESTIONS.md`](INTERVIEW_QUESTIONS.md) from memory.

## Tier 2 — Intermediate (a single Docker host)

**You need:** one Linux host with Docker installed (an EC2 instance is enough; no AWS-specific services required beyond the instance itself).

1. [`labs/03-volumes-and-persistence.md`](../labs/03-volumes-and-persistence.md) — all four storage types, sharing a volume across containers.
2. [`labs/04-networking.md`](../labs/04-networking.md) — default bridge vs. a user-defined bridge, container-to-container DNS by name.
3. [`labs/05-compose-multi-service-bank-app.md`](../labs/05-compose-multi-service-bank-app.md) — the four-module HDFC-style banking app as one Compose stack.
4. Read [`docs/STORAGE_AND_NETWORKING.md`](STORAGE_AND_NETWORKING.md) and [`docs/COMPOSE_AND_SWARM.md`](COMPOSE_AND_SWARM.md) (Compose section) in full.
5. Answer the Storage & Networking and Compose & Swarm sections of [`docs/INTERVIEW_QUESTIONS.md`](INTERVIEW_QUESTIONS.md).

## Tier 3 — Advanced (a 3-node cluster)

**You need:** 3 Linux hosts that can reach each other (3 EC2 instances in the same VPC/subnet is the cheapest path — a manager on `t2.medium`, two workers on `t2.micro`).

1. [`labs/06-swarm-ha-cluster.md`](../labs/06-swarm-ha-cluster.md) — bootstrap the cluster, deploy a replicated service, scale it, kill a replica and watch self-healing, roll an update back.
2. [`labs/07-jenkins-image-pipeline.md`](../labs/07-jenkins-image-pipeline.md) — install Jenkins on the manager, build the parameterized pipeline, push images to Docker Hub, deploy the full stack with `docker stack deploy`.
3. Read [`docs/CI_CD_PIPELINE.md`](CI_CD_PIPELINE.md) and [`docs/SECURITY.md`](SECURITY.md) in full, and check the deployed stack against the security checklist.
4. Work through every scenario in [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — try to reproduce at least #1, #2, #7, and #10 deliberately on your own cluster before reading the fix.
5. Answer the Security and Architect/SRE sections of [`docs/INTERVIEW_QUESTIONS.md`](INTERVIEW_QUESTIONS.md) without re-reading the earlier docs first.

## Cleanup, at any stage

```bash
docker kill $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi -f $(docker images -q)
docker system prune -a --volumes    # only if you're fully done with this repo's containers/images
```

On a Swarm cluster, tear down stacks/services before leaving the swarm:

```bash
docker stack rm bank
docker swarm leave --force   # on the manager, only once every node has left or been removed
```

If you launched EC2 instances for the Tier 3 labs, terminate them once you're done to avoid ongoing cost.
