#!/usr/bin/env -S /bin/bash
set -e
. /container-env.sh
if [ "$#" -eq 0 ]; then
  PORT=$(ocsprest config | jq .port)
  ocsprest -v refresher &
  gunicorn ocsprest.routes:app_factory --bind 0.0.0.0:$PORT -w 4 --worker-class aiohttp.GunicornWebWorker
else
  # run the given command
  exec "$@"
fi
