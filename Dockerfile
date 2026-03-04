# ============================================================
# Synapsa — Multi-Stage Dockerfile
# Optimized for minimal image size with GPU inference support
# ============================================================

# Stage 1: Builder — install dependencies
FROM python:3.10-slim AS builder

WORKDIR /build

# System dependencies for compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency specification
COPY pyproject.toml README.md ./
COPY synapsa/ ./synapsa/

# Install Python dependencies (without GPU libs — those are added at runtime)
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime — lean production image
FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY synapsa/ ./synapsa/
COPY configs/ ./configs/
COPY app_budowlanka.py ./
COPY pyproject.toml README.md ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash synapsa && \
    mkdir -p /app/synapsa_workspace /app/synapsa_memory && \
    chown -R synapsa:synapsa /app

USER synapsa

# Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app_budowlanka.py", "--server.port=8501"]
