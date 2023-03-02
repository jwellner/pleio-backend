import os
from enum import Enum

import clamd
from django.conf import settings


class FILE_SCAN(str, Enum):
    CLEAN = 'CLEAN'
    VIRUS = 'VIRUS'
    UNKNOWN = 'UNKNOWN'
    NOTFOUND = 'NOTFOUND'
    OFFLINE = 'OFFLINE'


class FileScanError(Exception):
    status = FILE_SCAN.UNKNOWN
    feedback = None

    def __init__(self, status, feedback):
        super().__init__(feedback)
        self.status = status
        self.feedback = feedback

    def is_virus(self):
        return self.status == FILE_SCAN.VIRUS

    def is_unknown(self):
        return self.status == FILE_SCAN.UNKNOWN

    def is_notfound(self):
        return self.status == FILE_SCAN.NOTFOUND

    def is_offline(self):
        return self.status == FILE_SCAN.OFFLINE


def skip_av():
    return not bool(settings.CLAMAV_HOST)


def scan(path):
    try:
        if skip_av():
            return FILE_SCAN.CLEAN

        if not os.path.exists(path):
            raise FileScanError(FILE_SCAN.NOTFOUND, "File not ready yet.")

        cd = clamd.ClamdNetworkSocket(host=settings.CLAMAV_HOST, timeout=120)
        with open(path, 'rb') as fh:
            result = cd.instream(fh)

        if result and result['stream'][0] == 'FOUND':
            raise FileScanError(FILE_SCAN.VIRUS, result['stream'][1])

        return FILE_SCAN.CLEAN
    except FileScanError:
        raise
    except clamd.ConnectionError:
        raise FileScanError(FILE_SCAN.OFFLINE, "CLAMAV is offline at the moment")
    except Exception as e:
        raise FileScanError(FILE_SCAN.UNKNOWN, "%s during virusscan: %s" % (e.__class__, str(e)))
