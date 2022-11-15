from django.conf import settings
from online_planner.settings_container import SettingsContainerBase

from core import config


class SettingsContainer(SettingsContainerBase):
    def get_key(self):
        return config.ONLINEAFSPRAKEN_KEY

    def get_secret(self):
        return config.ONLINEAFSPRAKEN_SECRET

    def get_url(self):
        return config.ONLINEAFSPRAKEN_URL or settings.ONLINE_MEETINGS_URL

    def get_video_api_url(self):
        return config.VIDEOCALL_API_URL or settings.VIDEO_CALL_RESERVE_ROOM_URL
