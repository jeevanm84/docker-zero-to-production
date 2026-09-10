# Docker Compose and Docker Swarm

## The problem before Compose

Take the HDFC-style example: four independent modules — `internetbanking`, `mobilebanking`, `insurance`, `loan` — each with its own `index.html` and its own Dockerfile:

```dockerfile
FROM ubuntu
RUN apt update -y
RUN apt install apache2 -y
COPY index.html /var/www/html
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
```

Running this by hand means four separate `docker build` + `docker run -p ...` invocations, four container names to remember, and no single command to bring the whole application up, down, or restarted together. That's fine for one container. It doesn't scale to a real application.

## Docker Compose

Docker Compose defines a **multi-container application on a single host** as one YAML file (`docker-compose.yml`), then brings the whole stack up or down with one command.

```yaml
version: '3.8'
services:
  internetbanking:
    image: internetbanking:v1
    ports:
      - "81:80"
  mobilebanking:
    image: mobilebanking:v1
    ports:
      - "82:80"
  insurance:
    image: insurance:v1
    ports:
      - "83:80"
  loan:
    image: loans:v1
    ports:
      - "84:80"
```

```bash
docker-compose up -d          # create and start every service, detached
docker-compose ps
docker-compose stop           # stop everything (or: docker-compose stop <service> for one)
docker-compose start
docker-compose logs
docker-compose top
docker-compose restart
docker-compose down           # stop and remove everything in one command
```

By default Compose looks for `docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, or `compose.yaml`. A different filename needs `-f`:

```bash
docker-compose -f reyaz.yml up -d
```

A full runnable version — four backend services behind an Nginx load balancer, and a separate Flask + Nginx variant — is in [`examples/compose/`](../examples/compose/).

### Compose's ceiling

`docker-compose scale loan=10` will try to create 10 replicas of the same service **on one host**, and immediately hits a port conflict because every replica wants the same published port. Compose has no concept of a multi-host cluster or automatic load balancing across replicas — that's exactly the gap Swarm (or Kubernetes) fills.

## Docker Swarm — orchestration and high availability

If a container dies, you can restart it. But if the entire **Docker host** dies, everything on it is gone until someone rebuilds it. Docker Swarm turns a group of Docker hosts into one managed cluster so that workloads survive individual node failure.

```
                 Docker Swarm Cluster

        ┌──────────────┬──────────────┐
        │              │              │
   Manager Node    Worker Node    Worker Node
        │              │              │
     Container      Container      Container
```

- A **manager node** schedules services and holds cluster state; **worker nodes** run the actual container tasks.
- Nodes join over port **2377**.
- Without Swarm: manual deployment, manual scaling, manual recovery. With Swarm: cluster management, auto-scheduling, self-healing, load balancing across replicas, rolling updates, high availability — all built in.

### Bootstrapping a cluster

```bash
# on the manager
docker swarm init
# copy the printed join token, then on each worker:
docker swarm join --token SWMTKN-1-... <manager-ip>:2377

# back on the manager
docker node ls
```

### Service vs. plain container

`docker run` on the manager only ever creates a container **on the manager**. To actually distribute work across the cluster, you create a **service**:

```bash
docker service create --name internetbanking --replicas 3 -p 81:80 trainerreyaz/ib-image:latest
docker service ls
docker service ps internetbanking
docker service logs internetbanking
docker service inspect internetbanking
```

Because Swarm sets up routing mesh networking, `http://<any-node-ip>:81` reaches the service regardless of which node actually happens to be running a given replica.

### Scaling, rollback, rolling updates

```bash
docker service scale internetbanking=10   # scale out, distributed across all nodes
docker service scale internetbanking=3    # scale down (LIFO)
docker service rollback internetbanking   # revert to the replica count/image before the last change

docker service update --image trainerreyaz/mb-image internetbanking   # rolling update, zero downtime
docker service rollback internetbanking                                # revert the image too
```

### Self-healing

Manually kill and remove a container backing a replicated service on a worker node — Swarm notices the desired state (`replicas: 3`) no longer matches reality and creates a replacement automatically. This is the core value proposition over plain Compose: Swarm continuously reconciles actual state toward desired state.

```bash
docker service rm internetbanking   # tear the service down entirely
```

### Global vs. replicated services

| | Replicated | Global |
|---|---|---|
| You specify | A desired replica **count** | Nothing — one task per node, automatically |
| Guarantee | *N* replicas total, distributed across available nodes (not guaranteed one-per-node) | Exactly one replica on **every** node |
| Node removed | Same total replica count redistributed to remaining nodes | Total replica count drops by one |
| Typical use | A web service scaled horizontally | A per-node agent — log collector, monitoring agent |

```bash
docker service create --name nginx-global --mode global --publish 80:80 nginx
```

### Cluster membership

```bash
docker swarm leave                  # run on a worker to leave the cluster
docker swarm join-token worker      # regenerate a worker join token
docker swarm join-token manager     # regenerate a manager join token
docker node rm <node-id>            # remove a node that's already down
docker swarm init --force-new-cluster   # recover if the whole swarm state is broken
```

### Docker Swarm secrets

Secrets (passwords, keys, certs) should never be baked into an image or passed as a plain environment variable in a Compose file. Swarm secrets are encrypted at rest and only exposed to the services that request them, mounted read-only at `/run/secrets/<name>` inside the container.

```bash
docker secret create db_password db_password.txt
docker secret ls
```

```yaml
services:
  db:
    image: postgres:latest
    environment:
      POSTGRES_USER: webuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_DB: webdatabase
    secrets:
      - db_password

secrets:
  db_password:
    file: db_password.txt
```

```bash
docker stack deploy --compose-file docker-compose.yml myapp
docker stack rm myapp
docker secret rm db_password
```

If the secret was created out-of-band (`docker secret create`, not via the Compose file), reference it as external instead of re-declaring its source file:

```yaml
secrets:
  db_password:
    external: true
```

Runnable example (Postgres + Adminer + a Swarm secret): [`examples/compose/swarm-stack-with-secrets/`](../examples/compose/swarm-stack-with-secrets/).

## Compose vs. Swarm vs. Stack

| | Docker Compose | Docker Swarm | Docker Stack |
|---|---|---|---|
| Scope | Single host | Multi-host cluster | Multi-host cluster |
| Typical use | Local dev, single-host deployments | Cluster management primitives (`docker service`) | Deploys a **Compose file** onto a Swarm cluster |
| Command | `docker compose up` | `docker service create` | `docker stack deploy -c file.yml <stack-name>` |
| Scaling across hosts | No | Yes | Yes |
| Built-in HA | No | Yes | Yes |
| Networking | Local bridge | Overlay | Overlay |

A **Stack** is the bridge between the two: the same Compose-file syntax you already know, deployed across an entire Swarm cluster with `docker stack deploy`.

```bash
docker stack ls
docker stack services <stack-name>
docker stack ps <stack-name>
docker stack rm <stack-name>
```

Note the practical limit reached here: **Swarm has no built-in autoscaling** (replica counts are set manually, not driven by load) and its load balancing is simple round-robin at the routing-mesh level, not metric-aware. That gap — plus a richer scheduling and networking model — is why production-grade clusters generally move to Kubernetes once a workload outgrows Swarm; Swarm's real strength is being dramatically simpler to stand up for small-to-mid clusters.

## Interview-ready answers

**Compose vs. Swarm?** Compose orchestrates multiple containers on one host from one YAML file. Swarm orchestrates services across a multi-host cluster, adding replication, self-healing, rolling updates, and overlay networking. A Stack deploys a Compose-syntax file *onto* a Swarm cluster.

**What is a replica?** One running instance (task) of a service. Multiple replicas give horizontal scaling and availability if a node or container fails.

**What is a rolling update?** Replacing a service's replicas gradually with a new image version, so the service stays available throughout instead of all replicas going down and back up at once.

**How do you roll back a failed update?** `docker service rollback <service>` — reverts to the previous replica configuration/image.
