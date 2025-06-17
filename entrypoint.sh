#!/bin/sh

# Export environment variables for the Python scripts
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Variables pour listenbrainz_sync.py
export LISTENBRAINZ_RUN_ONCE=${LISTENBRAINZ_RUN_ONCE:-"False"}
export LISTENBRAINZ_CRON_ENABLED=${LISTENBRAINZ_CRON_ENABLED:-"False"}
export LISTENBRAINZ_CRON_SCHEDULE=${LISTENBRAINZ_CRON_SCHEDULE:-"30 1 * * *"}
export LISTENBRAINZ_URL=${LISTENBRAINZ_URL:-""}
export LISTENBRAINZ_M3U_FILENAME=${LISTENBRAINZ_M3U_FILENAME:-"@Created for You.m3u8"}
export LISTENBRAINZ_BASE_PATH=${LISTENBRAINZ_BASE_PATH:-"/app/music"}

# Variable pour deemix
export DEEMIX_ARL=${DEEMIX_ARL:-""}

# Log the configuration
echo "Configuration:"
echo "  LOG_LEVEL=${LOG_LEVEL}"
echo "  LISTENBRAINZ_RUN_ONCE=${LISTENBRAINZ_RUN_ONCE}"
echo "  LISTENBRAINZ_CRON_ENABLED=${LISTENBRAINZ_CRON_ENABLED}"
echo "  LISTENBRAINZ_CRON_SCHEDULE=${LISTENBRAINZ_CRON_SCHEDULE}"
echo "  LISTENBRAINZ_URL=${LISTENBRAINZ_URL}"
echo "  LISTENBRAINZ_M3U_FILENAME=${LISTENBRAINZ_M3U_FILENAME}"
echo "  LISTENBRAINZ_BASE_PATH=${LISTENBRAINZ_BASE_PATH}"
echo "  DEEMIX_ARL=${DEEMIX_ARL}"

# Configure cron for listenbrainz_sync.py
if [ "$LISTENBRAINZ_CRON_ENABLED" = "True" ]; then
  echo "Configuring cron for listenbrainz_sync.py with schedule: ${LISTENBRAINZ_CRON_SCHEDULE}"
  
  echo "LOG_LEVEL=${LOG_LEVEL}" >> /etc/cron.d/lb-cron
  echo "LISTENBRAINZ_URL=${LISTENBRAINZ_URL}" >> /etc/cron.d/lb-cron
  echo "LISTENBRAINZ_M3U_FILENAME=${LISTENBRAINZ_M3U_FILENAME}" >> /etc/cron.d/lb-cron
  echo "LISTENBRAINZ_BASE_PATH=${LISTENBRAINZ_BASE_PATH}" >> /etc/cron.d/lb-cron
  echo "DEEMIX_ARL=${DEEMIX_ARL}" >> /etc/cron.d/lb-cron

  echo "${LISTENBRAINZ_CRON_SCHEDULE} /usr/local/bin/python3 /app/listenbrainz_sync.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/lb-cron

  chmod 0644 /etc/cron.d/lb-cron
  crontab /etc/cron.d/lb-cron
  touch /var/log/cron.log
  echo "Cron configured."
fi

# Start the cron daemon in the background
echo "Starting cron daemon..."
service cron start

# Execute listenbrainz_sync.py immediately if LISTENBRAINZ_RUN_ONCE is enabled
if [ "$LISTENBRAINZ_RUN_ONCE" = "True" ]; then
  echo "LISTENBRAINZ_RUN_ONCE is enabled. Running listenbrainz_sync.py immediately..."
  /usr/local/bin/python3 /app/listenbrainz_sync.py --source immediate
fi

# Keep the container running
echo "Tailing cron log to keep the container running..."
tail -f /var/log/cron.log