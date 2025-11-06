#!/bin/bash

echo "=== Azure Container Registry Authentication Setup for Kubernetes ==="

# Set kubeconfig path
KUBECONFIG_PATH="../skaffold/.kind-kubeconfig"

# Check if kubeconfig exists
if [[ ! -f "$KUBECONFIG_PATH" ]]; then
    echo "❌ Kubeconfig file not found at $KUBECONFIG_PATH"
    exit 1
fi

# Test kubectl connection
echo "Checking Kubernetes connection..."
if ! kubectl --kubeconfig="$KUBECONFIG_PATH" cluster-info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi
echo "✓ Connected to Kubernetes cluster"

echo ""
echo "Please provide your Azure Container Registry credentials:"
read -p "ACR Registry URL (e.g., ydigital.azurecr.io): " ACR_URL
read -p "ACR Username: " ACR_USERNAME
read -s -p "ACR Password/Token: " ACR_PASSWORD
echo ""

read -p "Namespace [default]: " NAMESPACE
NAMESPACE=${NAMESPACE:-default}

echo "Creating ACR secret in namespace '$NAMESPACE'..."
kubectl --kubeconfig="$KUBECONFIG_PATH" create secret docker-registry ydigitalregistry \
    --docker-server="$ACR_URL" \
    --docker-username="$ACR_USERNAME" \
    --docker-password="$ACR_PASSWORD" \
    --namespace="$NAMESPACE"

if [[ $? -eq 0 ]]; then
    echo "✓ ACR secret 'ydigitalregistry' created successfully in namespace '$NAMESPACE'"
else
    echo "❌ Failed to create ACR secret"
    exit 1
fi

echo ""
echo "=== Next Steps ==="
echo "1. Verify the secret:"
echo "   kubectl get secret ydigitalregistry -n $NAMESPACE --kubeconfig=$KUBECONFIG_PATH"
echo ""
echo "2. Restart failed pods:"
echo "   kubectl delete pods --selector=app=nextcloud-ingestor -n $NAMESPACE --kubeconfig=$KUBECONFIG_PATH"
echo ""
echo "✓ Setup complete!"