from http import HTTPStatus
import os.path

from django.http import Http404, HttpResponse
from django.template import loader
from django.utils import timezone


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


class BadRequestReact(HttpErrorReactPage):
    status_code = HTTPStatus.BAD_REQUEST


def file_blocked_response(request, filename, reason):
    content = loader.render_to_string(template_name="file_blocked.html",
                                      context={"filename": os.path.basename(filename),
                                               'reason': reason},
                                      request=request)

    return HttpResponse(content,
                        status=HTTPStatus.MULTIPLE_CHOICES,
                        headers={
                            'Expires': timezone.now().isoformat(),
                            'Pragma': 'no-cache',
                            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
                        })
