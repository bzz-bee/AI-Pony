class TooManyRequests(Exception):
    """Exception raised when too many requests are sent.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Too many requests, try again later."):
        super().__init__(message)


class PathNullError(Exception):
    """Exception raised when a null path is returned by the server.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="FakeYou.com returned a null path"):
        super().__init__(message)


class Dead(Exception):
    """Exception raised when the TTS job is dead and discarded by the server.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="TTS job is dead, Server discarded it"):
        super().__init__(message)


class RequestError(Exception):
    """Generic exception for request errors."""
    def __init__(self, message="An error occurred with the request"):
        super().__init__(message)


class Failed(Exception):
    """Exception raised for a general failure.

    Attributes:
        message (str): Suggestion to check token, text, file, or retry.
    """
    def __init__(self, message="Check token and text/file, or try again"):
        super().__init__(message)


class InvalidCredentials(Exception):
    """Exception raised for invalid credentials.

    Attributes:
        message (str): Suggestion to check username or password.
    """
    def __init__(self, message="Check username or password"):
        super().__init__(message)


class UserNotFound(Exception):
    """Exception raised when a user is not found.

    Attributes:
        username (str): Username that was not found.
    """
    def __init__(self, username):
        message = f"The user {username} not found"
        super().__init__(message)


class UsernameTooShort(Exception):
    """Exception raised when a username is too short.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Username too short"):
        super().__init__(message)


class UsernameTaken(Exception):
    """Exception raised when a username is already taken.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Username taken"):
        super().__init__(message)


class EmailTaken(Exception):
    """Exception raised when an email is already taken.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Email taken"):
        super().__init__(message)


class W2lTemplateTokenWrong(Exception):
    """Exception raised when the wrong w2l template token is used.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Wrong w2l template token"):
        super().__init__(message)


class PasswordTooShort(Exception):
    """Exception raised when a password is too short.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Password too short"):
        super().__init__(message)


class UnAuthorized(Exception):
    """Exception raised for unauthorized access."""
    def __init__(self, message="Unauthorized access"):
        super().__init__(message)


class TtsResultNotFound(Exception):
    """Exception raised when a TTS result is not found."""
    def __init__(self, message="TTS result not found"):
        super().__init__(message)


class EmailInvalid(Exception):
    """Exception raised for invalid email format.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message="Invalid email format"):
        super().__init__(message)