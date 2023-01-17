from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class PleioDevStaticFilesStorage(ManifestStaticFilesStorage):
    manifest_strict = False
