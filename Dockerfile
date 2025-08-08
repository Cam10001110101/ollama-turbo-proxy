# Use Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install UV package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using UV
RUN uv pip compile pyproject.toml | uv pip install --system -r -

# Copy application files
COPY ollama_cli_proxy.py ./
COPY start-ollama-turbo.sh ./

# Make start script executable
RUN chmod +x start-ollama-turbo.sh

# Install Ollama CLI (required for the proxy to work)
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://ollama.ai/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create .ollama directory for SSH keys
RUN mkdir -p /root/.ollama

# Expose the proxy port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the proxy server directly (not the shell script since we need to handle SSH keys differently)
CMD ["python", "ollama_cli_proxy.py"]