# Lab 6 — Swarm HA cluster

## Objective

Bootstrap a 3-node Docker Swarm cluster, deploy a replicated service, scale it, deliberately kill a replica and watch self-healing, perform a rolling update, and roll it back.

## Prerequisites

3 Linux hosts that can reach each other on port 2377 (three EC2 instances in the same VPC/security group is the cheapest path — e.g. `manager` on `t2.medium`, `worker1`/`worker2` on `t2.micro`). Docker installed on all three.

```bash
# on all 3 hosts
sudo yum install -y docker
sudo systemctl start docker
```

## Steps

### 1. Set hostnames (optional, for clarity)

```bash
# manager
sudo hostnamectl set-hostname manager
# worker1
sudo hostnamectl set-hostname worker1
# worker2
sudo hostnamectl set-hostname worker2
```

### 2. Bootstrap the cluster

```bash
# on manager
docker swarm init
# copy the printed `docker swarm join --token ...` command
```

```bash
# on worker1 and worker2, paste the join command:
docker swarm join --token SWMTKN-1-xxxxxxxx <manager-private-ip>:2377
```

```bash
# back on manager
docker node ls    # all 3 nodes should show, manager marked Leader
```

### 3. Deploy a replicated service

```bash
docker service create --name internetbanking --replicas 3 -p 81:80 trainerreyaz/ib-image:latest
docker service ls
docker service ps internetbanking
```

Hit `http://<any-node-public-ip>:81` from all three nodes — Swarm's routing mesh makes the service reachable from every node, regardless of which node actually runs a given replica.

### 4. Scale up and down

```bash
docker service scale internetbanking=10
docker service ps internetbanking      # replicas distributed across all 3 nodes
docker service scale internetbanking=3
```

### 5. Rolling update and rollback

```bash
docker service update --image trainerreyaz/mb-image internetbanking
curl http://<any-node-ip>:81           # now serving the new image, with no downtime
docker service ps internetbanking
docker service rollback internetbanking
curl http://<any-node-ip>:81           # back to the previous image
```

### 6. Self-healing

```bash
# on any worker node running a replica of internetbanking:
docker ps                              # find a container ID
docker kill <container-id>
docker rm <container-id>
docker ps -a                           # a NEW container appears automatically within seconds
```

### 7. Global service

```bash
docker service create --name nginx-global --mode global --publish 8081:80 nginx
docker service ps nginx-global         # exactly one task per node, no replica count to set
```

### 8. Cluster membership

```bash
# on worker2
docker swarm leave
# on manager
docker node ls                         # worker2 shows Down
docker node rm <worker2-node-id>
```

## Expected observations

- The service stays reachable on its published port from every node, not just the one running a given replica.
- Killing a replica's container directly does not remove it from the service — Swarm replaces it to restore the desired replica count.
- A rolling update replaces replicas gradually; `docker service rollback` reverts cleanly.

## Verification

```bash
docker service ls
docker service ps internetbanking
docker node ls
```

## Cleanup

```bash
docker service rm internetbanking nginx-global
# on each worker still joined:
docker swarm leave
# on manager, once workers have left:
docker swarm leave --force
```

Terminate the EC2 instances if they were launched specifically for this lab, to avoid ongoing cost.

## Extension exercise

Simulate a full node failure: stop the EC2 instance behind one worker entirely (not just `docker swarm leave`) while a replicated service has tasks on it, and observe how long it takes Swarm to notice and reschedule those tasks onto the remaining nodes. Compare that recovery time against what a self-managed restart script would have taken.
