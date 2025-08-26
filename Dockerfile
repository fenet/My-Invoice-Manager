#FROM python:3.11-slim

#RUN apt-get update && apt-get install -y --no-install-recommends \
#    libcairo2 \
#    libpango-1.0-0 \
#    libgdk-pixbuf2.0-0 \
#    libffi-dev \
#    && rm -rf /var/lib/apt/lists/*

#WORKDIR /app
#COPY requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt
#COPY . .

#ENV PORT=8000
#EXPOSE 8000

#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System packages WeasyPrint needs (Cairo, Pango, GDK-Pixbuf) + fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app
COPY . .

# Railway provides $PORT; default to 8080 for local/container runs
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]

