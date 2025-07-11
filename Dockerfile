FROM python:3.11-slim

# Install system dependencies needed for ping
RUN apt-get update && apt-get install -y \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create templates directory and copy template
RUN mkdir -p templates
COPY templates/ templates/

# Copy default configuration (can be overridden with volume mount)
COPY hosts.yaml .

# Create non-root user for security
RUN useradd -m -u 1000 pinguser && chown -R pinguser:pinguser /app
USER pinguser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "app.py"]
