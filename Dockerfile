FROM python:3.9-slim

# Install system dependencies in one layer, with cleanup
RUN apt-get update && apt-get install -y \
    cron \
    ffmpeg \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install deemix via pip
RUN pip install --no-cache-dir deemix

# Set working directory
WORKDIR /app

# Copy only requirements.txt to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY listenbrainz_sync.py entrypoint.sh crontab /app/

# Copy crontab file to cron directory and set permissions
RUN cp /app/crontab /etc/cron.d/crontab && \
    chmod 0644 /etc/cron.d/crontab

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set environment path
ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
