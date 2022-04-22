import logging

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from core.lib import tenant_schema

logger = logging.getLogger(__name__)

@csrf_exempt
def profile_updated(request):
    if request.method == 'POST' and request.POST.get('origin_token'):
        # pylint:disable=import-outside-toplevel
        from concierge.tasks import profile_updated_signal
        profile_updated_signal.delay(tenant_schema(), request.POST['origin_token'])
        return JsonResponse({'result': 'ok'})

    return HttpResponseBadRequest()
