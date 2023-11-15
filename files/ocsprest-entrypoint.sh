#!/usr/bin/env -S /bin/bash
set -e
. /container-env.sh
if [ "$#" -eq 0 ]; then
  ocsprest config
  ocsprest -vv serve
else
  # run the given command
  exec "$@"
fi
