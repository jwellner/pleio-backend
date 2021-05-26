from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core import config
from core.models import Comment, Entity
from user.models import User


def validate_flow_token(request):
    token = config.FLOW_TOKEN
    if not token:
        return False
    try:
        if str(request.META['HTTP_AUTHORIZATION']) == str('Bearer ' + token):
            return True
    except Exception:
        pass
    try:
        if str(request.META['headers']['Authorization']) == str('Bearer ' + token):
            return True
    except Exception:
        pass
    return False

@csrf_exempt
@require_http_methods(["POST"])
def add_comment(request):
    if not config.FLOW_ENABLED or not validate_flow_token(request):
        return JsonResponse({"error": "Bad request"}, status=400)

    description = request.POST.get("description", "")
    object_id = request.POST.get("container_guid", "")

    if not description or not object_id:
        return JsonResponse({"error": "Bad request"}, status=400)

    try:
        entity = Entity.objects.get_subclass(id=object_id)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Entity for flow comment does not exist"}, status=401)

    try:
        user = User.objects.get(id=config.FLOW_USER_GUID)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "User configured in flow does not exist"}, status=401)

    Comment.objects.create(
        container=entity,
        owner=user,
        description=description
    )

    return JsonResponse({"error": None, "status": "Comment created from flow"})
