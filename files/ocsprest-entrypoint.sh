#!/usr/bin/env -S /bin/bash
set -e
. /container-env.sh
if [ "$#" -eq 0 ]; then
  PORT=$(ocsprest config | jq .port)
  # We use *one* worker on purpose (otherwise would have to figure out how only one worker would handle refresh
  gunicorn ocsprest.routes:app_factory --bind 0.0.0.0:$PORT -w 1 --worker-class aiohttp.GunicornWebWorker
else
  # run the given command
  exec "$@"
fi
