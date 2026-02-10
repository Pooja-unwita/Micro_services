from cryptography.hazmat.primitives import serialization
from pathlib import Path
import jwt
from datetime import datetime, timedelta, timezone
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from Authentication_Service.models.models import JWKS  
import logging

logger = logging.getLogger('ray.serve')


ALGORITHM = "RS256"
ISSUER = "Auth_Service"
ACCESS_TOKEN_EXPIRE_MINUTES = 720 #12 hours

class JWTKeyManager:
    """Manages JWT signing keys and token creation."""

    def __init__(self, keys_dict: dict):
        try:
            if not keys_dict:
                logger.error("Keys dictionary cannot be empty")
                raise ValueError("Keys dictionary cannot be empty")
            self.keys_dict = keys_dict
            logger.info("JWTKeyManager initialized successfully with provided keys")
        except Exception as e:
            logger.error(f"Failed to initialize JWTKeyManager: {e}")
            raise

    async def load_private_key(self,path: str)-> rsa.RSAPrivateKey:
        """Load a PEM-encoded private key from a file."""
        try:
            with open(path, "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                )
            
        except Exception as e:
            logger.error(f"Failed to load private key from path")
            raise 

    async def load_public_key(self,path: str)-> rsa.RSAPublicKey:
        """Load a PEM-encoded public key from a file."""
        try:
            with open(path, "rb") as f:
                return serialization.load_pem_public_key(f.read())
        except Exception as e:
            logger.error("Failed to load public key from path")
            raise 

        
    async def get_active_signing_key(self)-> tuple[str, rsa.RSAPrivateKey]:
        """Retrieve the active signing key."""
        try:
            for kid, key in self.keys_dict.items():
                if key["active"]:
                    return kid, await self.load_private_key(key["private"])
            logger.error("No active signing key found")
            raise Exception("No active signing key found")
        except Exception as e:
            logger.error(f"Failed to get active signing key: {e}")
            raise


    async def create_access_token(self,payload: dict)-> str:
        """Create a JWT access token with the given payload."""
        try:
            kid, private_key = await self.get_active_signing_key()
            to_encode = payload.copy()
            if "exp" not in to_encode or to_encode["exp"] is None:
                exp_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                to_encode["exp"] = int(exp_time.timestamp())

               
            to_encode["iss"] = ISSUER
            token = jwt.encode(
                to_encode,
                private_key,
                algorithm=ALGORITHM,
                headers={"kid": kid}
            )
            logger.info("Access token created successfully")
            return token
            
        except Exception as e:
                logger.error(f"Failed to create access token: {e}")
                raise 

    async def int_to_base64(self,n: int) -> base64:
        """Convert an integer to a base64url-encoded string."""
        try:
            return base64.urlsafe_b64encode(
                n.to_bytes((n.bit_length() + 7) // 8, "big")
            ).decode("utf-8").rstrip("=")
        
        except Exception as e:
            logger.error(f"Failed to convert integer to base64: {e}")
            raise 


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
            logger.error(f"Failed to convert public key to JWK: {e}")
            raise 
    
    async def jwks(self)-> JWKS:
        """Expose the JSON Web Key Set (JWKS) endpoint."""
        try:
            jwks_keys = []
            for kid, key in self.keys_dict.items():
                public_key = await self.load_public_key(key["public"])
                jwks_keys.append(await self.public_key_to_jwk(public_key, kid))
            logger.info("JWKS generated successfully")
            return {"keys": jwks_keys}
        except Exception as e:
            logger.error(f"Failed to generate JWKS: {e}")
            raise 
    
    async def get_key_from_jwks(self, token: str):
        """Retrieve the signing key from JWKS based on the token's KID."""
        try:
            header = jwt.get_unverified_header(token)
            kid = header["kid"]

            jwks = await self.jwks()
            for key in jwks["keys"]:
                if key["kid"] == kid:
                    
                    return jwt.algorithms.RSAAlgorithm.from_jwk(key)
            logger.error("Signing key not found in JWKS")
            raise Exception("Signing key not found")
        except Exception as e:
            logger.error(f"Failed to get key from JWKS: {e}")
            raise