from django.contrib.staticfiles.storage import ManifestStaticFilesStorage as ManifestStaticFilesStorageBase


class ManifestStaticFilesStorage(ManifestStaticFilesStorageBase):
    manifest_strict = False
