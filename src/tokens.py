import time
import hashlib
import base64
from pydantic import BaseModel, PositiveInt, StrictStr

class Tokens:
    
    class TokenData(BaseModel):
        validity_period_seconds: PositiveInt
        token: StrictStr

    @staticmethod
    def generate_client_secret(client_info: str) -> bytes:
        return hashlib.sha256(client_info.encode()).digest()

    @staticmethod
    def generate_signature(message: str, unique_string: bytes) -> str:
        hash_obj = hashlib.sha256(unique_string + message.encode())
        return base64.urlsafe_b64encode(hash_obj.digest()).decode()

    @staticmethod
    def generate_signed_token(validity_period_seconds: int, unique_string: bytes, file_path: str) -> str:
        expiry_time = int(time.time()) + validity_period_seconds
        message = f"{expiry_time}:{file_path}"
        signature = Tokens.generate_signature(message, unique_string)
        token = base64.urlsafe_b64encode(f"{message}:{signature}".encode()).decode()
        return token

    @staticmethod
    def validate_token(token: str, unique_string: bytes, file_path: str) -> bool:
        try:
            decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
            expiry_time, path, signature = decoded_token.rsplit(':', 2)
            expected_signature = Tokens.generate_signature(f"{expiry_time}:{path}", unique_string)
            return signature == expected_signature and time.time() <= int(expiry_time) and path == file_path
        except Exception:
            return False
