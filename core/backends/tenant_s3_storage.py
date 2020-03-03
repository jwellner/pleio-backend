from storages.backends.s3boto3 import S3Boto3Storage
from django_tenants.utils import parse_tenant_config_path


class TenantS3Boto3Storage(S3Boto3Storage):

    @property  
    def location(self):
        _location = parse_tenant_config_path("")
        return _location
