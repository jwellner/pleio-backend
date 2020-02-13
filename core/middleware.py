from django.utils import timezone

class UserLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user
        if not user.is_authenticated:
            return response

        ten_minutes_ago = timezone.now() - timezone.timedelta(minutes=10)

        try:
            if user.profile.last_online and user.profile.last_online > ten_minutes_ago:
                return response

            user.profile.last_online = timezone.now()
            user.profile.save()
        except Exception:
            pass
        

        return response
