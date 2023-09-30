#!/usr/bin/env -S /bin/bash
set -e
. /container-env.sh
if [ "$#" -eq 0 ]; then
  . /cfssl-start.sh
else
  # run the given command
  exec "$@"
fi
