import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from tokens import Tokens

load_dotenv()

class FileServ:

    class AppConfig(BaseSettings):
        api_key: str = Field("", env="X-API-KEY")
        serve_path: str = Field("files", env="SERVE_PATH")
        token_expiry_seconds: int = Field(300, env="TOKEN_EXPIRY_SECONDS")
        log_level: str = Field("INFO", env="LOG_LEVEL")

    def __init__(self):
        self.settings = self.AppConfig()
        self.settings.serve_path = os.path.normpath(os.path.abspath(self.settings.serve_path))
        self.app = FastAPI()
        self.setup_logging()
        self.setup_routes()

    def setup_logging(self):
        logging.basicConfig(level=self.settings.log_level.upper())
        self.logger = logging.getLogger(__name__)

    def setup_routes(self):
        @self.app.get("/{file_path:path}")
        async def get_file(file_path: str, request: Request, token: str = None):
            self.logger.info(f"Received request for file: {file_path}")
            
            if self.settings.api_key:
                api_key = request.headers.get("X-API-Key")
                if api_key != self.settings.api_key:
                    self.logger.warning("Forbidden request with invalid API key.")
                    raise HTTPException(status_code=403, detail="Forbidden: Invalid API key")
            
            client_info = self.generate_client_info(request)
            client_secret = Tokens.generate_client_secret(client_info)

            if token is None:
                full_path = os.path.join(self.settings.serve_path, file_path)
                self.logger.debug(f"Full path to check: {full_path}")

                if not os.path.isfile(full_path):
                    self.logger.error(f"File not found: {full_path}")
                    raise HTTPException(status_code=404, detail="Path not found")

                token = Tokens.generate_signed_token(self.settings.token_expiry_seconds, client_secret, file_path)
                self.logger.info(f"Generated signed URL for file: {file_path}")
                return {"url": f"http://localhost:8000/{file_path}?token={token}"}
            
            if not Tokens.validate_token(token, client_secret, file_path):
                self.logger.warning(f"Invalid or expired token for file: {file_path}")
                raise HTTPException(status_code=403, detail="Invalid or expired token")
            
            full_path = os.path.join(self.settings.serve_path, file_path)
            self.logger.debug(f"Full path to check: {full_path}")
            if not os.path.isfile(full_path):
                self.logger.error(f"File not found: {full_path}")
                raise HTTPException(status_code=404, detail="Path not found")
            
            self.logger.info(f"Serving file: {full_path}")
            return FileResponse(full_path, media_type='application/octet-stream', filename=os.path.basename(full_path))

    def generate_client_info(self, request: Request) -> str:
        header_names = ['user-agent', 'accept-language', 'host']
        headers_string = ';'.join(request.headers.get(header, '') for header in header_names)
        client_ip = request.client.host
        return f"{client_ip};{headers_string}"

fileserv = FileServ()
app = fileserv.app
