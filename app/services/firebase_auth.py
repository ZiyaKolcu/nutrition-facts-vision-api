"""Firebase authentication service for token verification."""

import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from dotenv import load_dotenv


load_dotenv()


if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIAL_PATH"))
    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str) -> str:
    """
    Verifies the Firebase ID token and returns the corresponding Firebase UID.

    Args:
        id_token (str): The Firebase ID token sent from the client.

    Returns:
        str: The UID of the authenticated user.

    Raises:
        HTTPException: If the token is invalid or verification fails.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as exc:
        print(f"Firebase token verification error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token"
        ) from exc
