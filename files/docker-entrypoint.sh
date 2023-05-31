#!/bin/bash
set -e


# CA Cert key and config filen path
CFSLL_PERSISTENT_FOLDER="${CFSLL_PERSISTENT_FOLDER:-/data/persistent}"
RUN_CA="${RUN_CA:-/data/persistent/ca.pem}"
RUN_CA_KEY="${RUN_CA_KEY:-/data/persistent/ca_key.pem}"
RUN_CA_CONF="${RUN_CA_CONF:-/data/persistent/ca_conf.json}"
RUN_CA_CFSSL_CONF="${RUN_CA_CFSSL_CONF:-/data/persistent/root_ca_cfssl.json}"

RUN_INTER_CA="${RUN_INTER_CA:-/data/persistent/inter-ca.pem}"
RUN_INTER_CA_KEY="${RUN_INTER_CA_KEY:-/data/persistent/inter-ca_key.pem}"
RUN_INTER_CA_CONF="${RUN_INTER_CA_CONF:-/data/persistent/inter-ca_conf.json}"

# Root CA CSR config either in file or json string
# This configuration file contains "CSR" information.
INIT_CA_JSON_FILE="${INIT_CA_JSON_FILE:-/opt/cfssl/template/base_ca_conf.json}"
INIT_CA_JSON_STRING="${INIT_CA_JSON_STRING:-NA}"
# This configuration file contains "Certificate signing" information
INIT_CA_CONFIG_JSON_FILE="${INIT_CA_CONFIG_JSON_FILE:-/opt/cfssl/template/root_ca_cfssl.json}"

# Intermediate CA CSR configuration in file or json string
INIT_INTER_CA_JSON_FILE="${INIT_INTER_CA_JSON_FILE:-/opt/cfssl/template/base_inter_ca_conf.json}"
INIT_INTER_CA_JSON_STRING="${INIT_INTER_CA_JSON_STRING:-NA}"

# Alternative goose init config files can be changed using these.
INIT_GOOSE_DBJSON_FILE="${INIT_GOOSE_DBJSON_FILE:-NA}"
INIT_GOOSE_DBCONF_FILE="${INIT_GOOSE_DBCONF_FILE:-NA}"
INIT_GOOSE_CREATECERTIFICATES_SQL_FILE="${INIT_GOOSE_CREATECERTIFICATES_SQL_FILE:-NA}"
INIT_GOOSE_ADDMETADATA_SQL_FILE="${INIT_GOOSE_ADDMETADATA_SQL_FILE:-NA}"

INT_SHARED_CERT_FOLDER="${INT_SHARED_CERT_FOLDER:-/ca_public}"

#
# Run certificate init procedures if the CA file doesn't exists
#
if [[ ! -f "${RUN_CA}" ]]
then
    echo "$(date) --- Init CA certificates"
    mkdir -p "${CFSLL_PERSISTENT_FOLDER}"

    # Check the CA config source. It's either json string or file and copy it to place
    if [ "$INIT_CA_JSON_STRING" != "NA" ]
    then
        echo "$(date) --- Using INIT_CA_JSON_STRING variables as base config"
        if echo $INIT_CA_JSON_STRING | jq > /dev/null
        then
            echo "${INIT_CA_JSON_STRING}" > "$RUN_CA_CONF"
        else
            echo $INIT_CA_JSON_STRING | jq
            echo "$(date) --- ERROR - INIT_CA_JSON_STRING is not valid JSON"
            exit
        fi
    else
        if [[ -f "$INIT_CA_JSON_FILE" ]]
        echo "$(date) --- Using file defined in INIT_CA_JSON_FILE as base config"
        then
            if cat "$INIT_CA_JSON_FILE" | jq > /dev/null
            then
                cp "$INIT_CA_JSON_FILE" "$RUN_CA_CONF"
            else
                cat "$INIT_CA_JSON_FILE" | jq
                echo "$(date) --- ERROR - INIT_CA_JSON_FILE doesnt contain valid JSON"
                exit
            fi
        else
            echo "$(date) --- ERROR - INIT_CA_JSON_FILE not found"
            exit
        fi
    fi

    # Check the INTER CA config source. It's either json string or file and copy it to place
    if [ "$INIT_INTER_CA_JSON_STRING" != "NA" ]
    then
        echo "$(date) --- Using INIT_INTER_CA_JSON_STRING variables as base config"
        if echo $INIT_INTER_CA_JSON_STRING | jq > /dev/null
        then
            echo "${INIT_INTER_CA_JSON_STRING}" > "$RUN_INTER_CA_CONF"
        else
            echo $INIT_INTER_CA_JSON_STRING | jq
            echo "$(date) --- ERROR - INIT_INTER_CA_JSON_STRING is not valid JSON"
            exit
        fi

    else
        echo "$(date) --- Using file defined in INIT_CA_JSON_FILE as base config"
        if cat "$INIT_INTER_CA_JSON_FILE" | jq > /dev/null
        then
            cp "$INIT_INTER_CA_JSON_FILE" "$RUN_INTER_CA_CONF"
        else
            cat "$INIT_INTER_CA_JSON_FILE" | jq
            echo "$(date) --- ERROR - INIT_INTER_CA_JSON_FILE doesnt contain valid JSON"
            exit
        fi
    fi

    if cat "$INIT_CA_CONFIG_JSON_FILE" | jq > /dev/null
    then
        cp "$INIT_CA_CONFIG_JSON_FILE" "$RUN_CA_CFSSL_CONF"
    else
        cat "$INIT_CA_CONFIG_JSON_FILE" | jq
        echo "$(date) --- ERROR - INIT_CA_CONFIG_JSON_FILE doesnt contain valid JSON"
        exit
    fi




    # Generate new CA files
    pushd "${CFSLL_PERSISTENT_FOLDER}" > /dev/null
    cfssl gencert -initca "${RUN_CA_CONF}" | cfssljson -bare init_ca

    cfssl gencert -initca "${RUN_INTER_CA_CONF}" | cfssljson -bare init_intermediate_ca
    cfssl sign -ca init_ca.pem -ca-key init_ca-key.pem -config "${RUN_CA_CFSSL_CONF}" -profile intermediate_ca init_intermediate_ca.csr | cfssljson -bare init_intermediate_ca


    # Copy temporary CA files to persistent path
    cp init_ca.pem "${RUN_CA}"
    cp init_ca-key.pem "${RUN_INTER_CA_KEY}"
    cp init_intermediate_ca.pem "${RUN_INTER_CA}"
    cp init_intermediate_ca-key.pem "${RUN_INTER_CA_KEY}"

    popd > /dev/null
    echo "$(date) --- Init complete..."

fi


#
# Run goose init (copy files), use alternative files if one is defined in env vars...
#
if [[ ! -f "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/dbconf.yml" ]]
then
    echo "$(date) --- running first time goose init tasks..."
    mkdir -p "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/migrations"

    if [ "$INIT_GOOSE_DBJSON_FILE" != "NA" ]
    then
        cp "${INIT_GOOSE_DBJSON_FILE}" "${CFSLL_PERSISTENT_FOLDER}/db.json"
    else
        cp "/opt/cfssl/template/goose/db.json" "${CFSLL_PERSISTENT_FOLDER}/db.json"
    fi

    if [ "${INIT_GOOSE_DBCONF_FILE}" != "NA" ]
    then
        cp "${INIT_GOOSE_DBCONF_FILE}" "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/dbconf.yml"
    else
        cp "/opt/cfssl/template/goose/dbconf.yml" "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/dbconf.yml"
    fi

    if [ "${INIT_GOOSE_CREATECERTIFICATES_SQL_FILE}" != "NA" ]
    then
        cp "${INIT_GOOSE_CREATECERTIFICATES_SQL_FILE}" "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/migrations/001_CreateCertificates.sql"
    else
        cp "/opt/cfssl/template/goose/001_CreateCertificates.sql" "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/migrations/001_CreateCertificates.sql"
    fi

    if [ "${INIT_GOOSE_ADDMETADATA_SQL_FILE}" != "NA" ]
    then
        cp "${INIT_GOOSE_ADDMETADATA_SQL_FILE}" "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/migrations/002_AddMetadataToCertificates.sql"
    else
        cp "/opt/cfssl/template/goose/002_AddMetadataToCertificates.sql" "${CFSLL_PERSISTENT_FOLDER}/certdb/sqlite/migrations/002_AddMetadataToCertificates.sql"
    fi

fi

#
# Copy public certificates to shared folder
#

if [[ -f "${INT_SHARED_CERT_FOLDER}" ]]
then
    # Copy temporary CA files to persistent path
    cp "${RUN_CA}" "${INT_SHARED_CERT_FOLDER}/"
    cp "${RUN_INTER_CA}" "${INT_SHARED_CERT_FOLDER}/"
    cat "${RUN_CA}" "${RUN_INTER_CA}" >> "${INT_SHARED_CERT_FOLDER}/ca_chain.pem"
fi

#
# Run cfssl services
#
pushd "${CFSLL_PERSISTENT_FOLDER}" > /dev/null
echo "$(date) --- Starting sqlite goose addong"
goose -path certdb/sqlite up
echo "$(date) --- Running 'cfssl serve'"
cfssl serve -ca "${RUN_INTER_CA}" -ca-key "${RUN_INTER_CA_KEY}" -db-config "${CFSLL_PERSISTENT_FOLDER}/db.json"

#
# Exit/restart/crash
#
echo "$(date) --- docker-entrypoint.sh finished"
