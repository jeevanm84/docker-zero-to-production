# Demonstrates ENTRYPOINT (fixed) + CMD (default, overridable arguments).
# See docs/DOCKERFILE_REFERENCE.md for the full walkthrough.
#
#   docker run entrypoint-cmd-demo               -> Arguments passed: ['app.py', '--env=prod']
#   docker run entrypoint-cmd-demo --env=dev      -> Arguments passed: ['app.py', '--env=dev']
#
# ENTRYPOINT never changes; only CMD's default argument gets replaced.

FROM python:3.11-slim

WORKDIR /app
COPY app.py .

ENTRYPOINT ["python", "app.py"]
CMD ["--env=prod"]
