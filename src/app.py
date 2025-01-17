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
        api_key: str = Field("", env="API_KEY")
        serve_path: str = Field("files", env="SERVE_PATH")
        serve_domain: str = Field("localhost", env="SERVE_DOMAIN")
        serve_port: str = Field("8000", env="SERVE_PORT")
        token_expiry_seconds: int = Field(300, env="TOKEN_EXPIRY_SECONDS")
        log_level: str = Field("INFO", env="LOG_LEVEL")

    def __init__(self):
        self.settings = self.AppConfig()
        self.settings.serve_path = os.path.normpath(os.path.abspath(self.settings.serve_path))
        self.app = FastAPI()
        self.setup_logging()
        self.setup_routes()

        self.logger.info("Starting FileServ service...")
        self.logger.debug("Environment variables:")

        VALID_ENVIRONMENT_VARIABLES = [
            "API_KEY",
            "SERVE_PATH",
            "SERVE_DOMAIN",
            "SERVE_PORT",
            "TOKEN_EXPIRY_SECONDS",
            "LOG_LEVEL",
        ]

        for key, value in os.environ.items():
            if key in VALID_ENVIRONMENT_VARIABLES:
                self.logger.debug(f"{key}: {value}")

    def setup_logging(self):
        logging.basicConfig(level=self.settings.log_level.upper())
        self.logger = logging.getLogger(__name__)

    def setup_routes(self):

        @self.app.get("/health")
        async def health_check():
            return {"message": "OK", "status": 200}

        @self.app.get("/{file_path:path}")
        async def get_file(file_path: str, request: Request, token: str = None):

            self.logger.info(f"Request received - Path: {file_path}, Client: {request.client.host}")

            self.logger.debug(f"API Key configured: {bool(self.settings.api_key)}")
            self.logger.debug(f"API Key header present: {'X-API-Key' in request.headers}")
            self.logger.debug(f"Request headers: {dict(request.headers)}")

            if len(self.settings.api_key) > 0:
                if "X-API-Key" not in request.headers:
                    self.logger.warning(f"Access denied - Missing API key from {request.client.host}")
                    raise HTTPException(status_code=403, detail="Forbidden: Missing API key")
                if request.headers.get("X-API-Key") != self.settings.api_key:
                    self.logger.warning(f"Access denied - Invalid API key from {request.client.host}")
                    raise HTTPException(status_code=403, detail="Forbidden: Invalid API key")

            client_info = self.generate_client_info(request)
            client_secret = Tokens.generate_client_secret(client_info)

            if token is None:
                full_path = os.path.join(self.settings.serve_path, file_path)
                self.logger.debug(f"Validating file path: {full_path}")

                if not os.path.isfile(full_path):
                    self.logger.error(f"File not found: {full_path} (requested by {request.client.host})")
                    raise HTTPException(status_code=404, detail="Path not found")

                token = Tokens.generate_signed_token(self.settings.token_expiry_seconds, client_secret, file_path)
                self.logger.info(f"Generated access token for {file_path} (client: {request.client.host})")
                signed_url = f"http://{self.settings.serve_domain}:{self.settings.serve_port}/{file_path}?token={token}"
                self.logger.debug(f"Generated signed URL: {signed_url}")
                return signed_url

            if not Tokens.validate_token(token, client_secret, file_path):
                self.logger.warning(f"Invalid/expired token for {file_path} from {request.client.host}")
                raise HTTPException(status_code=403, detail="Invalid or expired token")

            full_path = os.path.join(self.settings.serve_path, file_path)
            self.logger.debug(f"Serving file from path: {full_path}")
            if not os.path.isfile(full_path):
                self.logger.error(f"File not found: {full_path} (requested by {request.client.host})")
                raise HTTPException(status_code=404, detail="Path not found")

            self.logger.info(f"Serving file: {file_path} to {request.client.host}")
            return FileResponse(
                full_path,
                media_type="application/octet-stream",
                filename=os.path.basename(full_path),
            )

    def generate_client_info(self, request: Request) -> str:
        header_names = ["user-agent", "accept-language", "host"]
        headers_string = ";".join(request.headers.get(header, "") for header in header_names)
        client_ip = request.client.host
        return f"{client_ip};{headers_string}"


fileserv = FileServ()
app = fileserv.app
app.state.fileserv = fileserv
