import json
import logging
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from core import config
from core.constances import ACCESS_TYPE
from core.lib import access_id_to_acl
from core.models import Group, ProfileField, UserProfileField
from file.models import FileFolder
from profile_sync.models import Logs
from user.models import User

logger = logging.getLogger(__name__)

def validate_token(request):
    token = config.PROFILE_SYNC_TOKEN
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


def serialize_user(user):

    profile = {}

    for field in ProfileField.objects.all():
        try:
            profile[field.key] = UserProfileField.objects.get(profile_field__key=field.key, user_profile=user.profile).value
        except ObjectDoesNotExist:
            profile[field.key] = ""

    return {
        "guid": user.guid,
        "external_id": user.custom_id,
        "name": user.name,
        "email": user.email,
        "is_member": True,
        "is_banned": not user.is_active,
        "time_created": user.created_at.isoformat(),
        "time_updated": user.updated_at.isoformat(),
        "icontime": None,
        "profile": profile
    }

# TODO: remove exempt?
@csrf_exempt
@require_http_methods(["POST", "GET"])
def users(request):
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    if not validate_token(request):
        return JsonResponse({
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
            },
            status=403
        )

    if request.method == 'GET':
        limit = 100
        if request.GET.get('limit'):
            limit=int(request.GET.get('limit'))

        created_at = datetime(1980, 1, 1)
        if request.GET.get('cursor'):
            try:
                created_at = User.objects.get(id=request.GET.get('cursor')).created_at
            except (ObjectDoesNotExist, ValidationError):
                return JsonResponse({
                    "error": "not_found",
                    "pretty_error": "Could not find user with this guid.",
                    "status": 404
                    },
                    status=404
                )

        serialized_users = []

        users = User.objects.filter(created_at__gt=created_at).order_by('created_at')[:limit]

        for user in users:
            serialized_users.append(serialize_user(user))

        return JsonResponse({"users": serialized_users}, status=200)

    if request.method == 'POST':
        data = json.loads(request.body)

        external_id = None
        if 'external_id' in data and data['external_id']:
            external_id = data['external_id'].strip()
        email = data['email'].strip()

        if 'guid' in data:
            user = User.objects.get(id=data['guid'])
            user.name = data['name']
            user.is_active = True
            if User.objects.filter(email__iexact=email).count() == 0:
                user.email = email
            elif (
                User.objects.filter(email__iexact=email).count() == 1
                and User.objects.filter(email__iexact=email).first() != user
            ):
                return JsonResponse({
                    "status": 400,
                    "error": "could_not_update",
                    "pretty_error": "Could not change the email to another email as the id is already taken.",
                    "user": {}
                    },
                    status=400
                )

            if external_id:
                if User.objects.filter(custom_id__iexact=external_id).count() == 0:
                    user.custom_id = external_id
                elif (
                    User.objects.filter(custom_id__iexact=external_id).count() == 1
                    and User.objects.filter(custom_id__iexact=external_id).first() != user
                ):
                    return JsonResponse({
                        "status": 400,
                        "error": "could_not_update",
                        "pretty_error": "Could not change the external_id to another external_id as the id is already taken.",
                        "user": {}
                        },
                        status=400
                    )
            user.save()

        if 'guid' not in data:
            if User.objects.filter(email__iexact=email).first():
                return JsonResponse({
                    "error": "could_not_create",
                    "pretty_error": "This e-mail is already taken by another user.",
                    "status": 400
                    },
                    status=400
                )

            if User.objects.filter(custom_id__iexact=external_id).first():
                return JsonResponse({
                    "error": "could_not_create",
                    "pretty_error": "This external_id is already taken by another user.",
                    "status": 400
                    },
                    status=400
                )

            try:
                user = User.objects.create(
                    name=data['name'],
                    email=email,
                    custom_id=external_id

                )
            except Exception as e:
                return JsonResponse({
                    "status": 400,
                    "error": "could_not_create",
                    "pretty_error": "Could not create the user with these attributes " + e,
                    "user": []
                    },
                    status=400
                )

        if 'groups' in data and data['groups']:
            for group_guid in data["groups"].split(sep=','):
                try:
                    group = Group.objects.get(id=group_guid)
                    if not group.is_full_member(user):
                        group.join(user)
                except Exception:
                    continue

        if 'profile' in data and data['profile']:
            for key, value in data['profile'].items():
                try:
                    profile_field = ProfileField.objects.get(key=key)
                    user_profile_field, created = UserProfileField.objects.get_or_create(
                        user_profile=user.profile,
                        profile_field=profile_field
                    )
                    user_profile_field.value = value
                    if created:
                        user_profile_field.read_access = access_id_to_acl(user, config.DEFAULT_ACCESS_ID)
                    user_profile_field.save()

                except Exception:
                    continue

        return JsonResponse({
            "status": 200,
            "user": serialize_user(user)
            },
            status=200
        )
    return JsonResponse({
            "status": 404
            },
            status=404
        )


# TODO: remove exempt?
@csrf_exempt
@require_http_methods(["DELETE"])
def users_delete(request, user_id):
    if not validate_token(request):
        return JsonResponse({
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
            },
            status=403
        )
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
            },
            status=404
        )

    user.delete()

    return JsonResponse({
        "status": 200
        },
        status=200
    )


# TODO: remove exempt?
@csrf_exempt
@require_http_methods(["POST"])
def ban_user(request, user_id):
    if not validate_token(request):
        return JsonResponse({
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
            },
            status=403
        )
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
            },
            status=404
        )

    user.is_active = False
    user.ban_reason = 'banned'
    user.save()

    return JsonResponse({
        "status": 200,
        "user": serialize_user(user)
        },
        status=200
    )


# TODO: remove exempt?
@csrf_exempt
@require_http_methods(["POST"])
def unban_user(request, user_id):
    if not validate_token(request):
        return JsonResponse({
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
            },
            status=403
        )
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
            },
            status=404
        )

    user.is_active = True
    user.ban_reason = ''
    user.save()

    return JsonResponse({
        "status": 200,
        "user": serialize_user(user)
        },
        status=200
    )

# TODO: remove exempt?
@csrf_exempt
@require_http_methods(["POST"])
def avatar_user(request, user_id):
    if not validate_token(request):
        return JsonResponse({
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
            },
            status=403
        )
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
            },
            status=404
        )

    try:
        avatar_file = FileFolder.objects.create(
            owner=user,
            upload=request.FILES['avatar'],
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(user.id)]
        )

        if user.profile.picture_file:
            if user.profile.picture_file.upload:
                user.profile.picture_file.upload.delete()
            if user.profile.picture_file.thumbnail:
                user.profile.picture_file.thumbnail.delete()
            user.profile.picture_file.delete()

        user.profile.picture_file = avatar_file
        user.profile.save()

    except Exception:
        return JsonResponse({
            "status": 404,
            "error": "not_saved",
            "pretty_error": "Could save avatar for user with this guid."
            },
            status=404
        )

    return JsonResponse({
        "status": 200,
        "user": serialize_user(user)
        },
        status=200
    )



# TODO: remove exempt?
@csrf_exempt
@require_http_methods(["POST"])
def logs(request):
    if not validate_token(request):
        return JsonResponse({
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
            },
            status=403
        )
    data = json.loads(request.body)

    if 'uuid' not in data:
        return JsonResponse({
            "error": "could_not_create",
            "pretty_error": "Could not create the log entry, uuid is missing.",
            "status": 400
            },
            status=400
        )

    try:
        uuid = data['uuid']
        content = data['content']
    except Exception:
        return JsonResponse({
            "error": "could_not_create",
            "pretty_error": "Invalid data",
            "status": 400
            },
            status=400
        )


    Logs.objects.create(uuid=uuid, content=content)

    return JsonResponse({
        "status": 200,
        "log": {"uuid": uuid}
        },
        status=200
    )
