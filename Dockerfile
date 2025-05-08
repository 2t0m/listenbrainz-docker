# Step to build the Docker image
FROM python:3.9-slim

# Install necessary dependencies, including cron and deemix
RUN apt-get update && apt-get install -y \
    cron \
    ffmpeg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install deemix via pip
RUN pip install --no-cache-dir deemix

# Set the working directory
WORKDIR /app

# Copy necessary files into the image
COPY listenbrainz_sync.py requirements.txt /app/
COPY entrypoint.sh /app/entrypoint.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and set the correct permissions
RUN chmod +x /app/entrypoint.sh

# Set the default command
CMD ["/app/entrypoint.sh"]
