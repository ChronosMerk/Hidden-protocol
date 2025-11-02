# --------------------------
# 📦 Dockerfile
# --------------------------

FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip --root-user-action=ignore \
 && pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["python", "app/main.py"]