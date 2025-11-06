#!/bin/bash
set -e

export GPT_API_KEY=$(pass y/bsw-passwords/GPT_API_KEY)
export GPT_EMBEDDINGS_KEY=$(pass y/develop-credentials/api/gpt/GPT4_TOKEN_1)
export MISTRAL_API_KEY=$(pass y/bsw-passwords/MISTRAL_API_KEY)
export VLAM_API_KEY=$(pass y/bsw-passwords/VLAM_API_KEY)
export HUGGINGFACE_HUB_TOKEN=$(pass y/bsw-passwords/HF_TOKEN)
export HF_TOKEN=$(pass y/bsw-passwords/HF_TOKEN)
export AZURE_STORAGE_CONNECTION_STRING=$(pass y/bsw-passwords/BLOB_STORAGE_CONNECTION_STRING)
export KC_ADMIN_USER=$(pass y/bsw-passwords/keycloak/KC_ADMIN_USER)
export KC_ADMIN_PASSWORD=$(pass y/bsw-passwords/keycloak/KC_ADMIN_PASSWORD)
export NC_ADMIN_USER=$(pass y/bsw-passwords/nextcloud/NC_ADMIN_USER)
export NC_ADMIN_PASSWORD=$(pass y/bsw-passwords/nextcloud/NC_ADMIN_PASSWORD)
export PG_USERNAME=$(pass y/bsw-passwords/postgres/PG_USERNAME)
export PG_PASSWORD=$(pass y/bsw-passwords/postgres/PG_PASSWORD)
export PG_OC_USER=$(pass y/bsw-passwords/postgres/PG_OC_USER)
export PG_OC_PASSWORD=$(pass y/bsw-passwords/postgres/PG_OC_PASSWORD)
export PG_ROOT_PASSWORD=$(pass y/bsw-passwords/postgres/PG_ROOT_PASSWORD)
export INGESTOR_DB_USER=$(pass y/bsw-passwords/postgres/PG_IN_USER)
export INGESTOR_DB_PASSWORD=$(pass y/bsw-passwords/postgres/PG_IN_PASSWORD)

export FRONTEND_TLS_CERT=$(pass y/bsw-passwords/tls/frontend-cert)
export FRONTEND_TLS_KEY=$(pass y/bsw-passwords/tls/frontend-key)

# export MSGRAPH_TENANT_ID=$(pass y/bsw-passwords/ingestor/MSGRAPH_TENANT_ID)
# export MSGRAPH_CLIENT_ID=$(pass y/bsw-passwords/ingestor/MSGRAPH_CLIENT_ID)
# export MSGRAPH_CLIENT_SECRET=$(pass y/bsw-passwords/ingestor/MSGRAPH_CLIENT_SECRET)


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
    --from-literal=root-password="$PG_ROOT_PASSWORD" \
    --from-literal=ingestor-user="$INGESTOR_DB_USER" \
    --from-literal=ingestor-password="$INGESTOR_DB_PASSWORD" \
    --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -

kubectl create secret tls bsw-tls-secret -n $NS \
    --cert=<(echo "$FRONTEND_TLS_CERT") \
    --key=<(echo "$FRONTEND_TLS_KEY") \
    --dry-run=client -o yaml | kubectl --kubeconfig .kind-kubeconfig apply -f -

echo "Secret values have been set."