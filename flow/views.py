import functools

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core import config
from core.lib import validate_token
from core.models import Comment, Entity
from user.models import User


def require_flow_token(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if not config.FLOW_ENABLED or not validate_token(request, config.FLOW_TOKEN):
            return JsonResponse({"error": "Bad request"}, status=400)
        return func(request, *args, **kwargs)

    return wrapper


@csrf_exempt
@require_flow_token
@require_http_methods(["POST"])
def add_comment(request):
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

    comment = Comment.objects.create(
        container=entity,
        owner=user,
        rich_description=description
    )

    return JsonResponse({"error": None, "status": "Comment created from flow", "comment_id": str(comment.id)})


@csrf_exempt
@require_flow_token
@require_http_methods(["POST"])
def edit_comment(request):
    description = request.POST.get("description", "")
    object_id = request.POST.get("container_guid", "")

    if not description or not object_id:
        return JsonResponse({"error": "Bad request"}, status=400)

    try:
        comment = Comment.objects.get(id=object_id)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Flow comment does not exist"}, status=401)

    comment.rich_description = description
    comment.save()

    return JsonResponse({"error": None, "status": "Comment edited from flow"}, status=200)
