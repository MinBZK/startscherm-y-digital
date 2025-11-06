from datetime import datetime, timezone
import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError
from typing import Dict, Any
from utils.logging.logger import logger

# Config
KEYCLOAK_SERVER_URL = (
    os.getenv("KEYCLOAK_SERVER_URL")
    or os.getenv("KEYCLOAK_INTERNAL_URL")
    or os.getenv("KEYCLOAK_URL")
    or "http://localhost:8080"
)
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "client-id")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_ISSUER = os.getenv(
    "KEYCLOAK_ISSUER", f"{KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}"
)

security = HTTPBearer()


class KeycloakAuth:
    def __init__(self):
        self.server_url = KEYCLOAK_SERVER_URL
        self.realm = KEYCLOAK_REALM
        self.client_id = KEYCLOAK_CLIENT_ID
        self.client_secret = KEYCLOAK_CLIENT_SECRET
        self._public_keys = None
        self._last_key_fetch = None

    @property
    def realm_url(self) -> str:
        return f"{self.server_url}/realms/{self.realm}"
    
    @property
    def certs_url(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/certs"
    
    @property
    def token_url(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/token"
    
    @property
    def userinfo_url(self) -> str:
        return f"{self.realm_url}/protocol/openid-connect/userinfo"
    
    async def get_public_keys(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        if (
            self._public_keys is None
            or self._last_key_fetch is None
            or (now - self._last_key_fetch).total_seconds() > 3600
        ):

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(self.certs_url, timeout=10.0)
                    response.raise_for_status()
                    self._public_keys = response.json()
                    self._last_key_fetch = now
                except httpx.HTTPError as e:
                    logger.error(
                        "Keycloak public key fetch failed: url=%s error=%s",
                        self.certs_url,
                        e,
                    )
                    raise HTTPException(
                        status_code=503,
                        detail=f"Failed to fetch public keys: {str(e)}",
                    )
        
        return self._public_keys
    
    async def verify_token(self, token: str) -> str:
        try:
            keys_data = await self.get_public_keys()

            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token header: 'kid' missing",
                )
            
            key = None
            for key_data in keys_data.get("keys", []):
                if key_data.get("kid") == kid:
                    key = key_data
                    break
            
            if not key:
                raise HTTPException(
                    status_code=401, detail="Public key not found"
                )
            
            issuer_expected = KEYCLOAK_ISSUER or self.realm_url
            try:
                payload = jwt.decode(
                    token,
                    key=key,
                    algorithms=["RS256"],
                    issuer=issuer_expected,
                    options={"verify_aud": False},
                )
            except JWTError as e:
                logger.warning("JWT decode failed: %s", e)
                raise

            aud = payload.get("aud")
            azp = payload.get("azp")
            client_ok = False
            if KEYCLOAK_CLIENT_ID:
                if aud is None:
                    client_ok = azp == KEYCLOAK_CLIENT_ID
                elif isinstance(aud, list):
                    client_ok = (
                        KEYCLOAK_CLIENT_ID in aud or azp == KEYCLOAK_CLIENT_ID
                    )
                else:
                    client_ok = (
                        aud == KEYCLOAK_CLIENT_ID or azp == KEYCLOAK_CLIENT_ID
                    )

            if not client_ok:
                logger.warning(
                    "Audience/azp mismatch aud=%s azp=%s expected=%s",
                    aud,
                    azp,
                    KEYCLOAK_CLIENT_ID,
                )
                raise HTTPException(status_code=401, detail="Invalid audience")
            user_info = {
                "user_id": payload.get("sub"),
                "username": payload.get("preferred_username"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
            }
            logger.info(f"Payload user info: {user_info}")
            if not user_info:
                raise HTTPException(
                    status_code=401, detail="Token missing user ID"
                )
            
            return user_info
        
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Token verification failed: {str(e)}",
            )


keycloak_auth = KeycloakAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    user_info = await keycloak_auth.verify_token(token)
    return user_info


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    userinfo = await get_current_user(credentials)
    userid = userinfo.get("username") or userinfo.get("user_id")
    return userid
