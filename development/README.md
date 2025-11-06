# Development Docker setup

Docker Compose stacks for isolated local services (postgres, elasticsearch, nextcloud, tika, keycloak). This is meant to set up independent instances of these services for local development, useful when not set up within the k8s cluster.

- The keycloak instance includes configuration for a bsw-realm with a default user for testing purposes.
- The nextcloud instance includes a init-users.sh script that sets up some default user accounts for testing purposes.