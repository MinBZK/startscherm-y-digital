#!/bin/bash
set -e

# load .env file if it exists
if [ -f "$(dirname "$0")/.env" ]; then
    export $(grep -v '^#' "$(dirname "$0")/.env" | xargs)

    # set default values if not set in .env
    if [ -z "$KC_ADMIN_USER" ]; then export KC_ADMIN_USER="kc_admin"; fi
    if [ -z "$KC_ADMIN_PASSWORD" ]; then export KC_ADMIN_PASSWORD="password"; fi
    if [ -z "$NC_ADMIN_USER" ]; then export NC_ADMIN_USER="admin"; fi
    if [ -z "$NC_ADMIN_PASSWORD" ]; then export NC_ADMIN_PASSWORD="password"; fi
    if [ -z "$PG_USERNAME" ]; then export PG_USERNAME="user"; fi
    if [ -z "$PG_PASSWORD" ]; then export PG_PASSWORD="password"; fi
    if [ -z "$PG_OC_USER" ]; then export PG_OC_USER="oc_admin"; fi
    if [ -z "$PG_OC_PASSWORD" ]; then export PG_OC_PASSWORD="password"; fi
    if [ -z "$INGESTOR_DB_USER" ]; then export INGESTOR_DB_USER="ingestor"; fi
    if [ -z "$INGESTOR_DB_PASSWORD" ]; then export INGESTOR_DB_PASSWORD="password"; fi

else
    echo "Warning: .env file not found in $(dirname "$0")" >&2
    echo "Trying to proceed with existing environment variables or load them using pass..." >&2


    set_env_from_pass() {
        local var_name=$1
        local pass_path=$2

        if [ -n "${!var_name}" ]; then
            echo "Info: Environment variable '$var_name' is already set." >&2
            return 0
        fi

        if ! command -v pass >/dev/null 2>&1; then
            echo "Warning: 'pass' command not found." >&2
            return 0
        fi

        if ! pass show "$pass_path" >/dev/null 2>&1; then
            echo "Warning: Password not found at path '$pass_path'." >&2
            return 0
        fi

        export "$var_name"="$(pass show "$pass_path")"
        echo "Set $var_name from pass."
        return 0

    }


    set_env_from_pass GPT_API_KEY y/bsw-passwords/GPT_API_KEY
    set_env_from_pass GPT_EMBEDDINGS_KEY y/develop-credentials/api/gpt/GPT4_TOKEN_1
    set_env_from_pass MISTRAL_API_KEY y/bsw-passwords/MISTRAL_API_KEY
    set_env_from_pass VLAM_API_KEY y/bsw-passwords/VLAM_API_KEY
    set_env_from_pass HUGGINGFACE_HUB_TOKEN y/bsw-passwords/HF_TOKEN
    set_env_from_pass AZURE_STORAGE_CONNECTION_STRING y/bsw-passwords/BLOB_STORAGE_CONNECTION_STRING

    set_env_from_pass KC_ADMIN_USER y/bsw-passwords/keycloak/KC_ADMIN_USER
    set_env_from_pass KC_ADMIN_PASSWORD y/bsw-passwords/keycloak/KC_ADMIN_PASSWORD

    set_env_from_pass NC_ADMIN_USER y/bsw-passwords/nextcloud/NC_ADMIN_USER
    set_env_from_pass NC_ADMIN_PASSWORD y/bsw-passwords/nextcloud/NC_ADMIN_PASSWORD

    set_env_from_pass PG_USERNAME y/bsw-passwords/postgres/PG_USERNAME
    set_env_from_pass PG_PASSWORD y/bsw-passwords/postgres/PG_PASSWORD
    set_env_from_pass PG_OC_USER y/bsw-passwords/postgres/PG_OC_USER
    set_env_from_pass PG_OC_PASSWORD y/bsw-passwords/postgres/PG_OC_PASSWORD
    set_env_from_pass INGESTOR_DB_USER y/bsw-passwords/postgres/PG_IN_USER
    set_env_from_pass INGESTOR_DB_PASSWORD y/bsw-passwords/postgres/PG_IN_PASSWORD

    set_env_from_pass FRONTEND_TLS_CERT y/bsw-passwords/tls/frontend-cert
    set_env_from_pass FRONTEND_TLS_KEY y/bsw-passwords/tls/frontend-key

fi


NS="default"

kubectl create secret generic api-llm-secrets -n $NS \
    --from-literal=gpt-api-key="$GPT_API_KEY" \
    --from-literal=gpt-embeddings-key="$GPT_EMBEDDINGS_KEY" \
    --from-literal=mistral-api-key="$MISTRAL_API_KEY" \
    --from-literal=vlam-api-key="$VLAM_API_KEY" \
    --from-literal=huggingface-token="$HUGGINGFACE_HUB_TOKEN" \
    --from-literal=azure-storage-connection-string="$AZURE_STORAGE_CONNECTION_STRING" \
    --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -

kubectl create secret generic keycloak-admin-secret -n $NS \
    --from-literal=admin-user="$KC_ADMIN_USER" \
    --from-literal=admin-password="$KC_ADMIN_PASSWORD" \
    --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -

kubectl create secret generic nextcloud-admin-secret -n $NS \
    --from-literal=admin-user="$NC_ADMIN_USER" \
    --from-literal=admin-password="$NC_ADMIN_PASSWORD" \
    --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -

kubectl create secret generic postgresql-secret -n $NS \
    --from-literal=username="$PG_USERNAME" \
    --from-literal=password="$PG_PASSWORD" \
    --from-literal=oc-user="$PG_OC_USER" \
    --from-literal=oc-password="$PG_OC_PASSWORD" \
    --from-literal=ingestor-user="$INGESTOR_DB_USER" \
    --from-literal=ingestor-password="$INGESTOR_DB_PASSWORD" \
    --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -


if [ ! -f "$FRONTEND_TLS_CERT" ] || [ ! -f "$FRONTEND_TLS_KEY" ]; then
    kubectl create secret tls bsw-tls-secret -n $NS \
        --cert=<(echo "$FRONTEND_TLS_CERT") \
        --key=<(echo "$FRONTEND_TLS_KEY") \
        --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -
else
    kubectl create secret tls bsw-tls-secret -n $NS \
        --cert=<(cat "$FRONTEND_TLS_CERT") \
        --key=<(cat "$FRONTEND_TLS_KEY") \
        --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -
fi

echo "Secret values have been set."