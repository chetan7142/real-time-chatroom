class BaseAppException(Exception):
    """Base exception for the application"""
    pass

class RoomNotFoundError(BaseAppException):
    """Raised when a room is not found"""
    pass

class UserNotFoundError(BaseAppException):
    """Raised when a user is not found"""
    pass

class UnauthorizedError(BaseAppException):
    """Raised when user doesn't have permission"""
    pass

class MessageNotFoundError(BaseAppException):
    """Raised when a message is not found"""
    pass

class FileNotFoundError(BaseAppException):
    """Raised when a file is not found"""
    pass

class NotificationNotFoundError(BaseAppException):
    """Raised when a notification is not found"""
    pass
