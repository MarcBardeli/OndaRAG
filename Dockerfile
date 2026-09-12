FROM node:22-bookworm-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python3 -m venv /opt/venv

# Usar el venv por defecto
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Aplicación
COPY . .

# Frontend compilado
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p audio knowledge .rag_index

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
