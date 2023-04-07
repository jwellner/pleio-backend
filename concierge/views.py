import logging

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from concierge.api import ApiTokenData
from core.lib import tenant_schema, tenant_summary
from user.models import User

logger = logging.getLogger(__name__)


@csrf_exempt
def profile_updated(request):
    if request.method == 'POST':
        try:
            api_data = ApiTokenData(request)
            api_data.assert_valid()

            user = User.objects.get(external_id=api_data.data['id'])

            # pylint:disable=import-outside-toplevel
            from concierge.tasks import profile_updated_signal
            profile_updated_signal.delay(tenant_schema(), user.guid)

            return JsonResponse({'result': 'ok'})
        except (AssertionError, User.DoesNotExist) as e:
            if settings.DEBUG:
                return HttpResponseBadRequest(str(e))

    return HttpResponseBadRequest()


def get_site_info(request):
    try:
        api_data = ApiTokenData(request)
        api_data.assert_valid()
        return JsonResponse(tenant_summary(with_favicon=True))
    except AssertionError:
        return HttpResponseBadRequest()


@csrf_exempt
def ban_user(request):
    try:
        assert request.method == 'POST'

        api_data = ApiTokenData(request)
        api_data.assert_valid()

        user = User.objects.get(Q(email=api_data.data['email']) | Q(external_id=api_data.data['id']))
        user.is_active = False
        user.ban_reason = api_data.data['reason']
        user.save()

    except AssertionError as e:
        if settings.DEBUG:
            return HttpResponseBadRequest(str(e))
        return HttpResponseBadRequest()

    except User.DoesNotExist:
        pass

    return JsonResponse({"result": "OK"})
