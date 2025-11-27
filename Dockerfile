# --------------------------
# 📦 Dockerfile
# --------------------------

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip --root-user-action=ignore \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "app/main.py"]