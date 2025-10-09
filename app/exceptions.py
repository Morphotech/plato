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


class PNGCompositionUnavailable(HTTPException):
    """
    Raised when the PNG composition service is temporarily unavailable
    """

    def __init__(self) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_501_NOT_IMPLEMENTED
        self.detail = "The PNG composition service is temporarily unavailable"


class UnsupportedResizingException(HTTPException):
    """
    Raised when the given mime type does not support resizing
    """

    def __init__(self, mime_type: str) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Resizing unsupported on provided mime_type: {mime_type}"


class SinglePageUnsupportedException(HTTPException):
    """
    Raised when the given mime type does not support single page printing
    """

    def __init__(self, mime_type: str) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"Single page printing unsupported on provided mime_type: {mime_type}"


class AspectRatioCompromisedException(HTTPException):
    """
    Raised when both height and width are specified, which compromises the template's aspect ratio
    """

    def __init__(self) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = "Specifying both width and height compromises the template's aspect ratio"


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


class InvalidPageNumberException(HTTPException):
    """
    Raised when the given page number is invalid, either by being a negative number or by
    being higher than the number of pages on the template
    """

    def __init__(self, page: int) -> None:
        """
        Constructor Method
        """
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = f"The page number is invalid: {page}"


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