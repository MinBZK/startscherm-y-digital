import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8082',
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'bsw-realm',
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'bsw-client'
});

export default keycloak;