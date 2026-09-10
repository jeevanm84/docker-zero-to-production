# Minimal static-site image served by Apache.
# Demonstrates: RUN layering, COPY, EXPOSE (documentation only), and why the
# main process must stay in the foreground (see docs/TROUBLESHOOTING.md #1).

FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y apache2 apache2-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY index.html /var/www/html/

EXPOSE 80

# -D FOREGROUND keeps Apache as PID 1 so the container stays alive and
# Apache's logs are visible via `docker logs`.
CMD ["/usr/sbin/apachectl", "-D", "FOREGROUND"]
