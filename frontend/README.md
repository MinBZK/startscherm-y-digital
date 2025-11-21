# BSW Frontend

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Local development

For local development, it is best to run the application using `npm run dev`. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

In order to make this work, you need the following setup:

- Run the API (`make develop` in the root of the BSW project);
- Port forward both the `bsw-api` and `bsw-keycloak` services (`make k9s` > `[shift] + F` on the service > `ok`);
- Run `npm install` / `pnpm install` in the frontend root;
- Set the following environment variables in the frontend root:

  ```bash
  #.env

  # Development Environment
  # Set to "development" to use mock data instead of API calls
  NEXT_PUBLIC_ENV=development

  # API Configuration
  # Base URL for the backend API
  NEXT_PUBLIC_API_BASE_URL=http://localhost:5000

  # Keycloak Authentication
  # Keycloak server URL (accessible from browser)
  NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8082

  # Keycloak realm name
  NEXT_PUBLIC_KEYCLOAK_REALM=bsw-realm

  # Keycloak client ID for the frontend application
  NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=bsw-client

  # Keycloak internal URL (for server-side requests)
  KEYCLOAK_INTERNAL_URL=http://localhost:8082

  # Keycloak container name (for Docker networking)
  KEYCLOAK_CONTAINER_NAME=keycloak

  # Nextcloud Integration
  # Nextcloud base URL for file sharing and browser links
  NEXT_PUBLIC_NEXTCLOUD_BASE_URL=http://localhost:8080
  ```
