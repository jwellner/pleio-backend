from django.db import models

# Migration helper models
class GuidMap(models.Model):
    id = models.BigAutoField(primary_key=True)
    guid = models.UUIDField(unique=True)
    object_type = models.CharField(max_length=32)

# Elgg Models
class Instances(models.Model):
    host = models.CharField(unique=True, max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.IntegerField(blank=True, null=True)
    env = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'instances'

class ElggAccessCollectionMembership(models.Model):
    user_guid = models.BigIntegerField(primary_key=True)
    access_collection_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_access_collection_membership'
        unique_together = (('user_guid', 'access_collection_id'),)


class ElggAccessCollections(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField()
    owner_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_access_collections'


class ElggAnnotations(models.Model):
    id = models.BigAutoField(primary_key=True)
    entity_guid = models.BigIntegerField()
    name_id = models.BigIntegerField()
    value_id = models.BigIntegerField()
    value_type = models.CharField(max_length=7)
    owner_guid = models.BigIntegerField()
    access_id = models.BigIntegerField()
    time_created = models.BigIntegerField()
    enabled = models.CharField(max_length=3)

    class Meta:
        managed = False
        db_table = 'elgg_annotations'


class ElggApiUsers(models.Model):
    id = models.BigAutoField(primary_key=True)
    site_guid = models.BigIntegerField(blank=True, null=True)
    api_key = models.CharField(unique=True, max_length=40, blank=True, null=True)
    secret = models.CharField(max_length=40)
    active = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elgg_api_users'


class ElggBackup(models.Model):
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(max_length=36)
    site_guid = models.BigIntegerField()
    time_created = models.BigIntegerField()
    performed_by = models.BigIntegerField()
    type = models.CharField(max_length=50)
    data = models.TextField()

    class Meta:
        managed = False
        db_table = 'elgg_backup'


class ElggConfig(models.Model):
    name = models.CharField(primary_key=True, max_length=255)
    value = models.TextField()
    site_guid = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_config'
        unique_together = (('name', 'site_guid'),)


class ElggDatalists(models.Model):
    name = models.CharField(primary_key=True, max_length=255)
    value = models.TextField()

    class Meta:
        managed = False
        db_table = 'elgg_datalists'


class ElggEntities(models.Model):
    guid = models.BigAutoField(primary_key=True, unique=True)
    type = models.CharField(max_length=6)

    #subtype = models.IntegerField(blank=True, null=True)
    subtype = models.OneToOneField('ElggEntitySubtypes', db_column='subtype', to_field='id', on_delete=models.CASCADE)

    owner_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField()
    container_guid = models.BigIntegerField()
    access_id = models.BigIntegerField()
    time_created = models.BigIntegerField()
    time_updated = models.BigIntegerField()
    last_action = models.BigIntegerField()
    enabled = models.CharField(max_length=3)

    def get_metadata_value_by_name(self, name):
        items = self.metadata.filter(name__string=name).all()

        data = None

        if items.count() > 1:
            data = []
            for item in items:
                data.append(item.value.string)
        elif items.count() == 1:
            data = items[0].value.string

        return data

    def get_private_value_by_name(self, name):
        item = self.private.filter(name=name).first()

        if item:
            return item.value

        return None

    class Meta:
        managed = False
        db_table = 'elgg_entities'


class ElggEntityRelationships(models.Model):
    id = models.BigAutoField(primary_key=True)
    # guid_one = models.BigIntegerField()
    left = models.ForeignKey('ElggEntities', db_column='guid_one', to_field='guid', on_delete=models.CASCADE, related_name='relation')

    relationship = models.CharField(max_length=50)
    #guid_two = models.BigIntegerField()
    right = models.ForeignKey('ElggEntities', db_column='guid_two', to_field='guid', on_delete=models.CASCADE, related_name='relation_inverse')

    time_created = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_entity_relationships'
        unique_together = (('left', 'relationship', 'right'),)


class ElggEntitySubtypes(models.Model):
    type = models.CharField(max_length=6)
    subtype = models.CharField(max_length=50)
    class_field = models.CharField(db_column='class', max_length=50)  # Field renamed because it was a Python reserved word.

    class Meta:
        managed = False
        db_table = 'elgg_entity_subtypes'
        unique_together = (('type', 'subtype'),)


class ElggEntityViews(models.Model):
    guid = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=6)
    subtype = models.IntegerField(blank=True, null=True)
    container_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField()
    views = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elgg_entity_views'


class ElggEntityViewsLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    entity_guid = models.BigIntegerField()
    type = models.CharField(max_length=6)
    subtype = models.IntegerField(blank=True, null=True)
    container_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField()
    performed_by_guid = models.BigIntegerField()
    time_created = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_entity_views_log'


class ElggGeocodeCache(models.Model):
    id = models.BigAutoField(primary_key=True)
    location = models.CharField(unique=True, max_length=128, blank=True, null=True)
    lat = models.CharField(max_length=20, blank=True, null=True)
    long = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elgg_geocode_cache'


class ElggGroupsEntity(models.Model):
    #guid = models.BigIntegerField(primary_key=True)
    entity = models.OneToOneField(ElggEntities, db_column='guid', to_field='guid', on_delete=models.CASCADE, primary_key=True)
    name = models.TextField()
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'elgg_groups_entity'


class ElggHmacCache(models.Model):
    hmac = models.CharField(primary_key=True, max_length=255)
    ts = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_hmac_cache'


class ElggMetadata(models.Model):
    id = models.BigAutoField(primary_key=True)
    #entity_guid = models.BigIntegerField()
    entity = models.ForeignKey('ElggEntities', db_column='entity_guid', to_field='guid', on_delete=models.CASCADE, related_name='metadata')
    #name_id = models.BigIntegerField()
    name = models.OneToOneField('ElggMetastrings', db_column='name_id', to_field='id', on_delete=models.CASCADE, related_name='metadata_name')
    #value_id = models.BigIntegerField()
    value = models.OneToOneField('ElggMetastrings', db_column='value_id', to_field='id', on_delete=models.CASCADE, related_name='metadata_value')
    value_type = models.CharField(max_length=7)
    owner_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField(blank=True, null=True)
    access_id = models.BigIntegerField()
    time_created = models.BigIntegerField()
    enabled = models.CharField(max_length=3)

    class Meta:
        managed = False
        db_table = 'elgg_metadata'


class ElggMetastrings(models.Model):
    id = models.BigAutoField(primary_key=True)
    string = models.TextField()

    class Meta:
        managed = False
        db_table = 'elgg_metastrings'


class ElggNotifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_guid = models.BigIntegerField()
    action = models.CharField(max_length=60, blank=True, null=True)
    performer_guid = models.BigIntegerField()
    entity_guid = models.BigIntegerField()
    container_guid = models.BigIntegerField()
    unread = models.CharField(max_length=3, blank=True, null=True)
    site_guid = models.BigIntegerField()
    time_created = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_notifications'


class ElggObjectsEntity(models.Model):
    #guid = models.BigIntegerField(primary_key=True)
    entity = models.OneToOneField(ElggEntities, db_column='guid', to_field='guid', on_delete=models.CASCADE, primary_key=True)

    title = models.TextField()
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'elgg_objects_entity'


class ElggPrivateSettings(models.Model):
    id = models.BigAutoField(primary_key=True)
    #entity_guid = models.BigIntegerField()
    entity = models.ForeignKey('ElggEntities', db_column='entity_guid', to_field='guid', on_delete=models.CASCADE, related_name='private')
    name = models.CharField(max_length=128)
    value = models.TextField()

    class Meta:
        managed = False
        db_table = 'elgg_private_settings'
        unique_together = (('entity', 'name'),)


class ElggPushNotificationsCount(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField()
    container_guid = models.BigIntegerField()
    count = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_push_notifications_count'
        unique_together = (('user_guid', 'container_guid'),)


class ElggPushNotificationsSubscriptions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_guid = models.BigIntegerField()
    client_id = models.CharField(max_length=100)
    service = models.CharField(max_length=4)
    device_id = models.CharField(max_length=100)
    token = models.CharField(max_length=512)

    class Meta:
        managed = False
        db_table = 'elgg_push_notifications_subscriptions'


class ElggRiver(models.Model):
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=8)
    subtype = models.CharField(max_length=32)
    action_type = models.CharField(max_length=32)
    site_guid = models.BigIntegerField()
    access_id = models.BigIntegerField()
    view = models.TextField()
    subject_guid = models.BigIntegerField()
    object_guid = models.BigIntegerField()
    annotation_id = models.BigIntegerField()
    posted = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_river'


class ElggSitesEntity(models.Model):
    #guid = models.BigIntegerField(primary_key=True)
    name = models.TextField()
    description = models.TextField()
    url = models.CharField(unique=True, max_length=255)

    entity = models.OneToOneField(ElggEntities, db_column='guid', to_field='guid', on_delete=models.CASCADE, primary_key=True)

    class Meta:
        managed = False
        db_table = 'elgg_sites_entity'


class ElggSystemLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    object_id = models.BigIntegerField()
    object_class = models.CharField(max_length=50)
    object_type = models.CharField(max_length=50)
    object_subtype = models.CharField(max_length=50)
    event = models.CharField(max_length=50)
    performed_by_guid = models.BigIntegerField()
    owner_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField(blank=True, null=True)
    access_id = models.BigIntegerField()
    enabled = models.CharField(max_length=3)
    time_created = models.BigIntegerField()
    ip_address = models.CharField(max_length=46)

    class Meta:
        managed = False
        db_table = 'elgg_system_log'


class ElggUsersApisessions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_guid = models.BigIntegerField()
    site_guid = models.BigIntegerField()
    token = models.CharField(max_length=40, blank=True, null=True)
    expires = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'elgg_users_apisessions'
        unique_together = (('user_guid', 'site_guid'),)


class ElggUsersEntity(models.Model):
    # guid = models.BigIntegerField(primary_key=True)
    entity = models.OneToOneField(ElggEntities, db_column='guid', to_field='guid', on_delete=models.CASCADE, primary_key=True)
    name = models.TextField()
    username = models.CharField(unique=True, max_length=128)
    password = models.CharField(max_length=32)
    salt = models.CharField(max_length=12)
    password_hash = models.CharField(max_length=256)
    email = models.TextField()
    language = models.CharField(max_length=6)
    code = models.CharField(max_length=32)
    banned = models.CharField(max_length=3)
    admin = models.CharField(max_length=3)
    last_action = models.BigIntegerField()
    prev_last_action = models.BigIntegerField()
    last_login = models.BigIntegerField()
    prev_last_login = models.BigIntegerField()
    pleio_guid = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elgg_users_entity'


class ElggUsersSessions(models.Model):
    session = models.CharField(primary_key=True, max_length=255)
    ts = models.BigIntegerField()
    data = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'elgg_users_sessions'


class OauthAccessTokens(models.Model):
    access_token = models.CharField(primary_key=True, max_length=40)
    client_id = models.CharField(max_length=80)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    expires = models.DateTimeField()
    scope = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_access_tokens'


class OauthAuthorizationCodes(models.Model):
    authorization_code = models.CharField(primary_key=True, max_length=40)
    client_id = models.CharField(max_length=80)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    redirect_uri = models.CharField(max_length=2000, blank=True, null=True)
    expires = models.DateTimeField()
    scope = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_authorization_codes'


class OauthClients(models.Model):
    client_id = models.CharField(primary_key=True, max_length=80)
    client_secret = models.CharField(max_length=80, blank=True, null=True)
    redirect_uri = models.CharField(max_length=2000)
    grant_types = models.CharField(max_length=80, blank=True, null=True)
    scope = models.CharField(max_length=100, blank=True, null=True)
    user_id = models.CharField(max_length=80, blank=True, null=True)
    gcm_key = models.CharField(max_length=100, blank=True, null=True)
    apns_cert = models.TextField(blank=True, null=True)
    wns_key = models.CharField(max_length=100, blank=True, null=True)
    wns_secret = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_clients'


class OauthJwt(models.Model):
    client_id = models.CharField(primary_key=True, max_length=80)
    subject = models.CharField(max_length=80, blank=True, null=True)
    public_key = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_jwt'


class OauthRefreshTokens(models.Model):
    refresh_token = models.CharField(primary_key=True, max_length=40)
    client_id = models.CharField(max_length=80)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    expires = models.DateTimeField()
    scope = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_refresh_tokens'


class OauthScopes(models.Model):
    scope = models.TextField(blank=True, null=True)
    is_default = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_scopes'


class OauthUsers(models.Model):
    username = models.CharField(primary_key=True, max_length=255)
    password = models.CharField(max_length=2000, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth_users'


class PleioRequestAccess(models.Model):
    id = models.BigAutoField(primary_key=True)
    guid = models.BigIntegerField(unique=True)
    user = models.TextField(blank=True, null=True)
    time_created = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pleio_request_access'


class ProfileSyncApiLog(models.Model):
    uuid = models.CharField(primary_key=True, max_length=36)
    content = models.TextField(blank=True, null=True)
    time_created = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'profile_sync_api_log'
