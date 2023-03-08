class InvalidFieldException(Exception):
    """
    Thrown when a requested field does not match expectations
    """


class IgnoreIndexError(Exception):
    """
    Thrown when an app does not control the given index
    """


class ExceptionDuringQueryIndex(Exception):
    """
    Thrown when sending a query to an index gives some kind of error.
    """


class UnableToTestIndex(Exception):
    """
    Thrown when a given index has no test.
    """


class AttachmentVirusScanError(Exception):
    """
    Thrown when a virus is found in an attachment.
    """
