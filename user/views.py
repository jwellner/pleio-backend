from django.http import StreamingHttpResponse

from core.constances import USER_ROLES
from core.http import ForbiddenReact, UnauthorizedReact, NotAllowedReact, BadRequestReact, NotFoundReact
from user.exception import ExportError
from user.exporting import ExportUsers
from user.models import User


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export(request):
    # Method not tested...
    user = request.user

    if not user.is_authenticated:
        raise UnauthorizedReact("Not logged in")

    if not user.has_role(USER_ROLES.ADMIN):
        raise NotAllowedReact("Not admin")

    user_fields = request.GET.getlist('user_fields[]')
    profile_field_guids = request.GET.getlist('profile_field_guids[]')

    if not user_fields and not profile_field_guids:
        raise BadRequestReact("No fields passed")

    export_users = ExportUsers(User.objects.get_filtered_users(include_superadmin=False).order_by('created_at'),
                               user_fields=user_fields,
                               profile_field_guids=profile_field_guids)

    try:
        response = StreamingHttpResponse(
            streaming_content=export_users.stream(buffer=Echo()),
            content_type='text/csv',
        )
        response['Content-Disposition'] = 'attachment;filename=exported_users.csv'
        return response
    except ExportError as e:
        raise BadRequestReact(str(e))

