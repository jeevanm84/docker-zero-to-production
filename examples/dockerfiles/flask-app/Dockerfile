# Demonstrates cache-friendly layer ordering: dependencies are copied and
# installed BEFORE the application source, so editing app.py never
# invalidates the (slow) pip install layer. See docs/TROUBLESHOOTING.md #4.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
