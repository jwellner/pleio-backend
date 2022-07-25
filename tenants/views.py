from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, StreamingHttpResponse
from django_tenants.utils import schema_context

from core.constances import USER_ROLES
from core.lib import get_mimetype
from tenants.models import AgreementVersion

def site_agreement_version_document(request, slug=None):
    user = request.user

    if not user.is_authenticated:
        raise Http404("File not found")

    if not user.has_role(USER_ROLES.ADMIN):
        raise Http404("File not found")

    if not slug:
        raise Http404("File not found")

    try:
        with schema_context('public'):
            agreement_version = AgreementVersion.objects.get(slug=slug)

            document = agreement_version.document

            response = StreamingHttpResponse(streaming_content=document.open(), content_type=get_mimetype(document.path))
            response['Content-Length'] = document.size
            response['Content-Disposition'] = f"attachment; filename=%s" % document.name
            return response

    except ObjectDoesNotExist:
        raise Http404("File not found")