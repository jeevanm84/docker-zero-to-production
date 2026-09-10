# Lab 7 — Jenkins image pipeline

## Objective

Install Jenkins on the Swarm manager from Lab 6, build a parameterized pipeline that checks out source, builds a chosen module's image, tags it, pushes it to Docker Hub, and deploys the full four-module stack to the Swarm cluster with `docker stack deploy`.

## Prerequisites

Lab 6's 3-node Swarm cluster, still running. A Docker Hub account. Read [`docs/CI_CD_PIPELINE.md`](../docs/CI_CD_PIPELINE.md) first — this lab builds exactly what that doc describes.

## Steps

### 1. Install Jenkins on the manager node

```bash
docker run -itd --name jenkins -p 8080:8080 jenkins/jenkins:lts
docker logs jenkins   # grab the initial admin password from the startup log
```

Browse to `http://<manager-ip>:8080`, unlock with that password, install suggested plugins.

### 2. Let Jenkins run Docker commands on the host

```bash
sudo chmod 777 /var/run/docker.sock
sudo systemctl daemon-reload
sudo systemctl restart docker.service
```

See `docs/CI_CD_PIPELINE.md` for the least-privilege alternative (`usermod -aG docker jenkins`) to prefer outside a lab environment.

### 3. Store the Docker Hub password as a Jenkins environment variable

**Manage Jenkins → System → Environment variables** → add `password` = `<your Docker Hub password or access token>`. Never put this value directly in the pipeline script.

### 4. Create the parameterized pipeline

New Item → Pipeline → check **This project is parameterized**:

- Choice parameter `image`: `internetbanking:v1`, `mobilebanking:v1`, `insurance:v1`, `loans:v1`
- Choice parameter `repo`: `<your-dockerhub-username>/ib-image`, `<your-dockerhub-username>/mb-image`, `<your-dockerhub-username>/insurance-image`, `<your-dockerhub-username>/loans-image`

Paste the pipeline script from [`examples/jenkins/Jenkinsfile`](../examples/jenkins/Jenkinsfile) (checkout → build → tag → push → deploy), pointing `checkout` at your own fork of the four-module bank source.

### 5. Run it once per module

Run the pipeline with `image=internetbanking:v1`, `repo=<you>/ib-image`. Confirm on Docker Hub that the image landed. Repeat for `mobilebanking`, `insurance`, `loan`, changing the module's `index.html` content between runs so each pushed image is visibly distinct.

### 6. Confirm the deploy stage

```bash
docker stack ls
docker stack services bank
docker stack ps bank
curl http://<any-node-ip>:81   # internetbanking
curl http://<any-node-ip>:84   # loan
```

### 7. Break something on purpose, then fix it through the pipeline

Change `insurance/index.html`, re-run the pipeline with `image=insurance:v1`, `repo=<you>/insurance-image`. Confirm `docker service update` rolled the new version out with no downtime on the other three modules.

## Expected observations

- One pipeline definition builds four different images, driven entirely by parameters — no duplicated pipeline logic per module.
- The `deploy` stage targets the whole Swarm cluster (`docker stack deploy`), not just the Jenkins host.
- Nothing in this setup triggers automatically on a `git push` — every build is a deliberate, parameterized, manually-triggered action (see `docs/CI_CD_PIPELINE.md` for why that's intentional here).

## Verification

```bash
docker service ls
docker stack ps bank
```

## Cleanup

```bash
docker stack rm bank
docker rm -f jenkins
```
Then follow Lab 6's cleanup for the underlying Swarm cluster and EC2 instances if you're fully done.

## Extension exercise

Add a `scan` stage between `build` and `tag` that runs `docker scout cves $image` (or `trivy image $image`) and fails the pipeline on high-severity CVEs — wiring the security scanning from `docs/SECURITY.md` directly into the delivery pipeline.
