from http import HTTPStatus

from django.http import Http404


class HttpErrorReactPage(Http404):
    status_code = None


class NotFoundReact(HttpErrorReactPage):
    status_code = HTTPStatus.NOT_FOUND


class UnauthorizedReact(HttpErrorReactPage):
    status_code = HTTPStatus.UNAUTHORIZED


class ForbiddenReact(HttpErrorReactPage):
    status_code = HTTPStatus.FORBIDDEN


class NotAllowedReact(HttpErrorReactPage):
    status_code = HTTPStatus.METHOD_NOT_ALLOWED
