# Troubleshooting

Incident-style scenarios: symptom → root cause → fix → why it happens.

## 1. Container exits immediately after `docker run`

**Symptom:** `docker ps` shows nothing; `docker ps -a` shows the container `Exited (0)` seconds after starting.

**Root cause:** the main process (PID 1) exited. A common cause is running a daemonizing process (like Apache without `-D FOREGROUND`, or `nginx` without `daemon off;`) — the process backgrounds itself, PID 1 exits, and Docker tears the container down because it only stays "running" while PID 1 is alive.

**Fix:** run the process in the foreground as the container's main command:

```dockerfile
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
# or
CMD ["nginx", "-g", "daemon off;"]
```

Check with `docker logs <container>` first — it usually shows exactly why the process exited (a config error, a missing file) rather than a silent daemonize.

## 2. `docker attach` then `exit` kills the container

**Symptom:** you `docker attach`ed to check on a container, typed `exit`, and now it's stopped.

**Root cause:** `docker attach` connects your terminal to the container's **main process (PID 1)**. Running `exit` inside that shell terminates PID 1 — the container stops, exactly like closing the one process keeping it alive.

**Fix:** detach without stopping the container using `Ctrl+P, Ctrl+Q`. If you need to run an additional command without touching the main process, use `docker exec -it <container> /bin/bash` instead — `exec` starts a **separate** process, and exiting that shell does not stop the container.

## 3. `EXPOSE 8080` in the Dockerfile but the app isn't reachable from outside

**Symptom:** `curl http://<host>:8080` fails, but `docker exec` into the container shows the app running and listening.

**Root cause:** `EXPOSE` is documentation only — it does not publish a port. Nothing binds the container's 8080 to the host.

**Fix:** publish the port explicitly:

```bash
docker run -p 8080:8080 myimage
```

or in Compose:

```yaml
ports:
  - "8080:8080"
```

## 4. Rebuilding a Dockerfile is much slower than expected after a tiny code change

**Symptom:** changing one line of application code causes a multi-minute rebuild, reinstalling all dependencies from scratch.

**Root cause:** `COPY . .` appears before the dependency-install step, so *any* file change (including unrelated source files) invalidates the cache for every instruction from that `COPY` onward — including the expensive `pip install`/`npm install` layer.

**Fix:** copy and install dependencies first, copy the rest of the source after:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

## 5. `docker build` context is enormous / build is slow to even start

**Symptom:** "Sending build context to Docker daemon" reports hundreds of MB before the build even begins.

**Root cause:** no `.dockerignore` — `.git`, `node_modules`, build artifacts, and logs are all being sent to the daemon as part of the build context.

**Fix:** add a `.dockerignore` excluding `.git`, `node_modules`, `target/`, `*.log`, and similar.

## 6. A service in Compose can't reach another service by name

**Symptom:** `nginx.conf` proxies to `backend1:5000`, and the container reports "could not resolve host `backend1`".

**Root cause:** either the two services aren't on the same Compose network (rare — Compose puts all services in one project on a shared network by default), or the service **name** in `docker-compose.yml` doesn't match the hostname used in config, or the service the other one depends on hasn't started yet.

**Fix:** confirm the service name in `docker-compose.yml` matches exactly what's referenced in config, and add `depends_on` so dependency ordering is explicit (note: `depends_on` controls start order, not "wait until actually ready" — for a hard readiness dependency, add a healthcheck).

## 7. A killed container in a Swarm service reappears — but a killed standalone container does not

**Symptom:** `docker kill` + `docker rm` on a container backing a Swarm **service** results in a brand-new container appearing seconds later; doing the same to a plain `docker run` container just leaves it gone.

**Root cause:** this is expected, not a bug. A Swarm **service** continuously reconciles actual replica count against the desired `--replicas` count — that's self-healing by design. A plain container created with `docker run` has no such controller watching it.

**Fix (if you actually want it gone):** remove the service itself, not just the container:

```bash
docker service rm <service-name>
```

## 8. `docker service scale app=10` doesn't work the way Compose's `scale` did

**Symptom:** scaling a Compose service to 10 replicas with `docker-compose` (not Swarm) fails with a port conflict.

**Root cause:** Compose runs everything on **one host**; 10 replicas of a service all trying to bind the same published host port collide immediately. Compose has no cross-host distribution or load-balancing layer.

**Fix:** use Swarm (`docker service scale <service>=10`) or Kubernetes, both of which distribute replicas across nodes and load-balance across them, instead of trying to scale via Compose.

## 9. Volume data isn't where you expect after switching mount types

**Symptom:** files written earlier via a named volume don't appear after switching a container to a bind mount (or vice versa), even though the container path looks the same.

**Root cause:** a named volume, an anonymous volume, and a bind mount are three different storage backends. A named volume lives under `/var/lib/docker/volumes/<name>/_data`; a bind mount is a specific host path you chose; they are not interchangeable just because the *container-side* path matches.

**Fix:** `docker inspect <container>` and check the `Mounts` section — confirm `Type` (`volume`/`bind`/`tmpfs`) and `Source` explicitly rather than assuming based on the container path alone.

## 10. Jenkins pipeline fails at the `docker build` stage with a permission error

**Symptom:** `permission denied while trying to connect to the Docker daemon socket`.

**Root cause:** the user Jenkins runs as doesn't have access to `/var/run/docker.sock`.

**Fix:** add the Jenkins user to the `docker` group (preferred) or, for a disposable lab host, `chmod 777 /var/run/docker.sock` followed by `systemctl restart docker.service` — see `docs/CI_CD_PIPELINE.md` for the trade-off between these two.
