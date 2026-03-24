import os.path
from app.constants import DRIVE_SCOPES

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.external_account_authorized_user import (
    Credentials as ExternalAccountAuthorized,
)
import logging


logger: logging.Logger = logging.getLogger(name=__name__)

class DriveCredentialsGetter:
    def __init__(self) -> None:
        self.creds:Credentials = self._get_drive_credentials()

    def _get_drive_credentials(self) -> Credentials:
        logger.info("getting google drive credentials")
        BASE_DIR: str = os.path.dirname(os.path.abspath(path=__file__))
        TOKEN_PATH: str = os.path.abspath(
            path=os.path.join(BASE_DIR, "../../app/creds/google/token.json")
        )
        creds: Credentials | ExternalAccountAuthorized | None = None

        if os.path.exists(path=TOKEN_PATH):
            logger.info("token file exist found start authentication")
            creds = Credentials.from_authorized_user_file(
                filename=TOKEN_PATH, scopes=DRIVE_SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.warning("cred was expired getting new token")
                creds.refresh(request=Request())
                with open(TOKEN_PATH, "w") as token:
                    token.write(creds.to_json())  # type: ignore
            elif not creds:
                raise ValueError("google Token file not exist")
        logger.info("token file is up to date")
        return creds  # type: ignore


def make_google_token_file() -> Credentials:
    logger.info("getting google drive credentials")
    BASE_DIR: str = os.path.dirname(os.path.abspath(path=__file__))
    TOKEN_PATH: str = os.path.abspath(
        path=os.path.join(BASE_DIR, "../../app/creds/google/token.json")
    )
    CREDS_PATH:str = os.path.abspath(
        path=os.path.join(BASE_DIR, "../../app/creds/google/credentials.json")
    )
    creds: Credentials | ExternalAccountAuthorized | None = None

    flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file=CREDS_PATH, scopes=DRIVE_SCOPES
    )
    creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(file=TOKEN_PATH, mode="w") as token:
        token.write(creds.to_json())
    return creds  # type: ignore

