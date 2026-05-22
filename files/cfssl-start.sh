#!/usr/bin/env -S /bin/bash
set -e

. /cfssl-init.sh

#
# Run cfssl services
#
pushd "${CFSSL_PERSISTENT_FOLDER}" > /dev/null
echo "$(date) --- Starting sqlite goose addong"
goose -dir certdb/sqlite/migrations sqlite3 certstore_development.db up
echo "$(date) --- Running 'cfssl serve'"
RESPONDER_FLAGS=""
if [ "$CFSSL_OCSP_ENABLED" = "true" ]; then
    RESPONDER_FLAGS="-responder=${RUN_OCSP_CERT} -responder-key=${RUN_OCSP_KEY}"
fi
cfssl serve -address=$CFSSL_BIND_ADDRESS -port $CFSSL_BIND_PORT \
  -ca "${RUN_INTER_CA}" -ca-key "${RUN_INTER_CA_KEY}" \
  -db-config "${RUN_DB_CONFIG}" \
  $RESPONDER_FLAGS \
  -int-bundle "${RUN_INTER_CA}" -ca-bundle "${RUN_CA}" \
  -loglevel 0
# If we give this config to serve we get [WARNING] failed to sign request: {"code":5100,"message":"Invalid policy: no key usage available"}
# But when we use it at CLI it works fine. WTF....
#   -config "${RUN_CA_CFSSL_CONF}" \

#
# Exit/restart/crash
#
echo "$(date) --- cfssl-start.sh finished"
