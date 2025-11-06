#!/bin/bash

# Script to create Docker Hub authentication secret for Kubernetes

set -e

echo "=== Docker Hub Authentication Setup for Kubernetes ==="
echo

# Check if kubectl is available
if ! command -v kubectl >/dev/null 2>&1; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "Make sure your kubectl context is set correctly"
    exit 1
fi

echo "✓ Connected to Kubernetes cluster"
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at: $ENV_FILE"
    echo "Please create a .env file with the following variables:"
    echo "DOCKER_USERNAME=your_username"
    echo "DOCKER_PASSWORD=your_password_or_token"
    exit 1
fi

# Load environment variables from .env file
echo "Loading Docker Hub credentials from .env file..."
set -a  # automatically export all variables
source "$ENV_FILE"
set +a  # disable automatic export

if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
    echo "❌ DOCKER_USERNAME and DOCKER_PASSWORD must be set in .env file"
    exit 1
fi

# Use default namespace
NAMESPACE="default"
echo "Using namespace: $NAMESPACE"

# Create the secret
echo "Creating Docker Hub secret in namespace '$NAMESPACE'..."

kubectl create secret docker-registry dockerhub-secret \
    --docker-server=https://index.docker.io/v1/ \
    --docker-username="$DOCKER_USERNAME" \
    --docker-password="$DOCKER_PASSWORD" \
    --docker-email="$DOCKER_USERNAME@example.com" \
    --namespace="$NAMESPACE" \
    --kubeconfig="../skaffold/.kind-kubeconfig" \
    --dry-run=client -o yaml | kubectl apply -f - \
    --kubeconfig="../skaffold/.kind-kubeconfig"

if [ $? -eq 0 ]; then
    echo "✓ Docker Hub secret 'dockerhub-secret' created successfully in namespace 'default'"
else
    echo "❌ Failed to create Docker Hub secret"
    exit 1
fi

echo
echo "=== Next Steps ==="
echo "1. Update your values.yaml to include the Docker Hub secret:"
echo "   imagePullSecrets:"
echo "     - name: dockerhub-secret"
echo "     - name: ydigitalregistry  # Keep your existing registry"
echo
echo "2. Or deploy with the secret:"
echo "   helm install bsw-stack ./deploy/helm --set imagePullSecrets[0].name=dockerhub-secret"
echo
echo "3. Verify the secret:"
echo "   kubectl get secret dockerhub-secret -n default"
echo
echo "✓ Setup complete!"