from cryptography.hazmat.primitives import serialization
from pathlib import Path
import jwt
from datetime import datetime, timedelta, timezone
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from Authentication_Service.models.models import JWKS  
# this has to given as relative path from where the script is run
KEYS = {
    "key-1": {
        "private": "Authentication_Service/keys/key1_private.pem",
        "public": "Authentication_Service/keys/key1_public.pem",
        "active": False,
    },
    "key-2": {
        "private": "Authentication_Service/keys/key2_private.pem",
        "public": "Authentication_Service/keys/key2_public.pem",
        "active": True,
    }
}
# check whether this has to be in config file
ALGORITHM = "RS256"
ISSUER = "Auth_Service"
ACCESS_TOKEN_EXPIRE_MINUTES = 720 #12 hours

class JWTKeyManager:
    """Manages JWT signing keys and token creation."""

    def __init__(self):
        pass

    async def load_private_key(self,path: str)-> rsa.RSAPrivateKey:
        """Load a PEM-encoded private key from a file."""
        try:
            with open(path, "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                )
        except Exception as e:
            raise e

    async def load_public_key(self,path: str)-> rsa.RSAPublicKey:
        """Load a PEM-encoded public key from a file."""
        try:
            with open(path, "rb") as f:
                return serialization.load_pem_public_key(f.read())
        except Exception as e:
            raise e

        
    async def get_active_signing_key(self)-> tuple[str, rsa.RSAPrivateKey]:
        """Retrieve the active signing key."""

        for kid, key in KEYS.items():
            if key["active"]:
                return kid, await self.load_private_key(key["private"])
        raise Exception("No active signing key found")


    async def create_access_token(self,payload: dict)-> str:
        """Create a JWT access token with the given payload."""
        try:
            kid, private_key = await self.get_active_signing_key()
            to_encode = payload.copy()
            to_encode.update({
                "iss": ISSUER,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            })
            token = jwt.encode(
                to_encode,
                private_key,
                algorithm=ALGORITHM,
                headers={"kid": kid}
            )
            return token
        
        except Exception as e:
            raise e

    async def int_to_base64(self,n: int) -> base64:
        """Convert an integer to a base64url-encoded string."""
        try:
            return base64.urlsafe_b64encode(
                n.to_bytes((n.bit_length() + 7) // 8, "big")
            ).decode("utf-8").rstrip("=")
        
        except Exception as e:
            raise e


    async def public_key_to_jwk(self,public_key, kid: str)-> dict:
        """Convert a public key to its JWK representation."""
        try:
            numbers = public_key.public_numbers()

            return {
                "kty": "RSA",
                "kid": kid,
                "use": "sig",
                "alg": "RS256",
                "n": await self.int_to_base64(numbers.n),
                "e": await self.int_to_base64(numbers.e),
            }
        except Exception as e:
            raise e
    
    async def jwks(self)-> JWKS:
        """Expose the JSON Web Key Set (JWKS) endpoint."""
        try:
            jwks_keys = []
            for kid, key in KEYS.items():
                public_key = await self.load_public_key(key["public"])
                jwks_keys.append(await self.public_key_to_jwk(public_key, kid))
            return {"keys": jwks_keys}
        except Exception as e:
            raise e
    
    async def get_key_from_jwks(self, token: str):
        """Retrieve the signing key from JWKS based on the token's KID."""
        header = jwt.get_unverified_header(token)
        kid = header["kid"]

        jwks = await self.jwks()
        for key in jwks["keys"]:
            if key["kid"] == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        raise Exception("Signing key not found")