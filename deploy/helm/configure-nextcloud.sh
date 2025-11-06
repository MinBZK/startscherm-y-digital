#!/bin/bash

# Helper script to configure NextCloud external access for development

echo "=== NextCloud External Configuration Helper ==="
echo

# Detect host IP
if command -v ip >/dev/null 2>&1; then
    # Linux
    HOST_IP=$(ip route get 1.1.1.1 | grep -oP 'src \K\S+')
elif command -v ifconfig >/dev/null 2>&1; then
    # macOS/BSD
    HOST_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
else
    HOST_IP="<UNKNOWN>"
fi

echo "Detected host IP: $HOST_IP"
echo

# Check if NextCloud is running
echo "Checking if NextCloud is accessible..."
if curl -f -s "http://localhost:8080/status.php" >/dev/null 2>&1; then
    echo "✓ NextCloud is running on localhost:8080"
else
    echo "✗ NextCloud is not accessible on localhost:8080"
    echo "  Start it with: cd development/nextcloud && docker-compose up -d"
fi
echo

# Check if NextCloud is accessible from external IP
if [ "$HOST_IP" != "<UNKNOWN>" ] && [ "$HOST_IP" != "127.0.0.1" ]; then
    echo "Checking if NextCloud is accessible from external IP..."
    if curl -f -s "http://$HOST_IP:8080/status.php" >/dev/null 2>&1; then
        echo "✓ NextCloud is accessible from $HOST_IP:8080"
    else
        echo "✗ NextCloud is not accessible from $HOST_IP:8080"
        echo "  This might be due to:"
        echo "  1. Firewall blocking port 8080"
        echo "  2. NextCloud trusted domains configuration"
        echo "  3. Docker networking issues"
    fi
    echo
fi

echo "=== Configuration for values.yaml ==="
echo
cat << EOF
nextcloud_ingestor:
  nextcloud:
    external:
      enabled: true
      ip: "$HOST_IP"
      port: 8080
  initJob:
    waitForNextcloud: true  # Enable waiting for NextCloud
EOF

echo
echo "=== Next Steps ==="
echo "1. Start NextCloud: cd development/nextcloud && docker-compose up -d"
echo "2. Update your values.yaml with the configuration above"
echo "3. Deploy with Helm: helm install/upgrade your-release ."
echo "4. Check logs: kubectl logs job/nextcloud-ingestor-init"