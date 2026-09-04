from fastapi import HTTPException
from starlette import status

class UnsupportedMIMEType(HTTPException):
    """
    Raised when the mime type requested is not supported
    """

    def __init__(self, mime_type: str) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        self.detail = f"The given mime type '{mime_type}' is not supported."


class TemplateNotFoundException(HTTPException):
    """
    Raised when the requested template cannot be found
    """

    def __init__(self, template_id: str) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = f"Template '{template_id}' not found"


class JSONSchemaVerificationErrorException(HTTPException):
    """
    Raised when the verification for the given JSON schema fails
    """

    def __init__(self) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "JSON schema validation failed"