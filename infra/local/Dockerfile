FROM python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY . /app
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "packages.api.gateway:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
