from django.utils.timezone import localtime
from online_planner.video_call import get_video_call_params

from core.models import VideoCall, VideoCallGuest
from core.resolvers import shared


def resolve_mutation_initiate_videocall(_, info, userGuid):
    shared.assert_videocall_enabled()
    shared.assert_videocall_profilepage()
    shared.assert_videocall_limit()

    user = info.context["request"].user
    shared.assert_authenticated(user)

    guest = shared.load_user(userGuid)

    params = get_video_call_params(dict(
        date=localtime().date().isoformat(),
        start_time=localtime().strftime("%H:%M"),
        meeting_host_name=user.name,
        meeting_guest_name=guest.name
    ))

    videocall = VideoCall.objects.create(
        user=user,
        host_url=params['VideoCallHostURL'],
        guest_url=params['VideoCallGuestURL']
    )
    videocall.send_notification()

    guestvideocall = VideoCallGuest.objects.create(
        video_call=videocall,
        user=guest
    )
    guestvideocall.send_notification()

    return {
        "success": True,
        "hostUrl": params['VideoCallHostURL'],
        "guestUrl": params['VideoCallGuestURL']
    }
