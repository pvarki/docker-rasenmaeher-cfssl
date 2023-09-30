#!/usr/bin/env -S /bin/bash
set -e

. /cfssl-init.sh

#
# Run cfssl services
#
pushd "${CFSSL_PERSISTENT_FOLDER}" > /dev/null
echo "$(date) --- Starting sqlite goose addong"
goose -path certdb/sqlite up
echo "$(date) --- Running 'cfssl serve'"
cfssl serve -address=$CFSSL_BIND_ADDRESS -port $CFSSL_BIND_PORT \
  -ca "${RUN_INTER_CA}" -ca-key "${RUN_INTER_CA_KEY}" \
  -db-config "${CFSSL_PERSISTENT_FOLDER}/db.json" \
  -responder="${RUN_OCSP_CERT}" -responder-key="${RUN_OCSP_KEY}" \
  -int-bundle "${RUN_INTER_CA}" -ca-bundle "${RUN_CA}" \
  -loglevel 0


#
# Exit/restart/crash
#
echo "$(date) --- cfssl-start.sh finished"
