# Lab 5 — Compose multi-service bank app

## Objective

Deploy four independent microservices (`internetbanking`, `mobilebanking`, `insurance`, `loan`) as one Compose stack, replacing four sets of manual `docker build`/`docker run` commands with a single `docker-compose.yml`.

## Prerequisites

Labs 1–4 completed. Docker Compose installed:

```bash
sudo dnf install libxcrypt-compat -y
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version
```

(Modern Docker installs typically include `docker compose` — the plugin form — already; either works for this lab.)

## Steps

### 1. See the manual, pre-Compose approach first (one module)

```bash
mkdir -p bank/internetbanking && cd bank/internetbanking
echo "<h1>Internet Banking</h1>" > index.html
cat > Dockerfile <<'EOF'
FROM ubuntu
RUN apt update -y
RUN apt install apache2 -y
COPY index.html /var/www/html
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
EOF
docker build -t internetbanking:v1 .
docker run -itd --name cont1 -p 81:80 internetbanking:v1
curl http://localhost:81
docker kill cont1 && docker rm cont1
```

Repeat by hand for `mobilebanking` (82), `insurance` (83), `loan` (84) — notice how repetitive and error-prone this gets. That repetition is exactly what Compose replaces.

### 2. Build all four images

```bash
cd ~/bank
for svc in internetbanking mobilebanking insurance loan; do
  mkdir -p $svc && echo "<h1>${svc}</h1>" > $svc/index.html
  cp internetbanking/Dockerfile $svc/Dockerfile 2>/dev/null || true
done
# ensure each has a Dockerfile identical to the one above, then:
(cd internetbanking && docker build -t internetbanking:v1 .)
(cd mobilebanking && docker build -t mobilebanking:v1 .)
(cd insurance && docker build -t insurance:v1 .)
(cd loan && docker build -t loans:v1 .)
```

### 3. Use the Compose file instead

Copy [`examples/compose/hdfc-bank-modules/docker-compose.yml`](../examples/compose/hdfc-bank-modules/docker-compose.yml) into `~/bank/`, then:

```bash
docker-compose up -d
docker-compose ps
curl http://localhost:81   # internetbanking
curl http://localhost:82   # mobilebanking
curl http://localhost:83   # insurance
curl http://localhost:84   # loan
```

### 4. Operate the stack as one unit

```bash
docker-compose stop loan        # stop just one service
docker-compose start loan
docker-compose logs
docker-compose top
docker-compose restart
```

### 5. Try scaling (and see where Compose's ceiling is)

```bash
docker-compose up -d --scale loan=3   # fails / conflicts on the published host port
```

This is expected — see `docs/COMPOSE_AND_SWARM.md` for why Compose can't do this cleanly and Lab 6 (Swarm) can.

### 6. Rename the Compose file and use `-f`

```bash
mv docker-compose.yml reyaz.yml
docker-compose up -d           # errors — default filenames not found
docker-compose -f reyaz.yml up -d
docker-compose -f reyaz.yml ps
```

## Expected observations

- One `docker-compose up -d` replaces four separate `docker build`/`docker run` sequences.
- `docker-compose down` stops and removes every service's container in one command.
- Scaling a service beyond 1 replica on a single host hits a port conflict — Compose has no cross-host distribution.

## Verification

```bash
docker-compose ps
docker ps -a
```

## Cleanup

```bash
docker-compose -f reyaz.yml down
docker rmi -f internetbanking:v1 mobilebanking:v1 insurance:v1 loans:v1
```

## Extension exercise

Build [`examples/compose/flask-nginx-lb/`](../examples/compose/flask-nginx-lb/) instead — three replicas of the same Flask backend behind an Nginx load balancer defined via `upstream` in `nginx.conf`. Send it a batch of requests and confirm all three backends show up:

```bash
for i in $(seq 1 20); do curl -s http://localhost; echo; done | sort | uniq -c
```

Nginx round-robins per **worker process**, so a handful of rapid sequential requests can briefly favor one backend before the distribution evens out across a larger batch — not a bug, just how multi-worker round robin behaves.
