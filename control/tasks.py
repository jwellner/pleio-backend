from __future__ import absolute_import, unicode_literals

import os
import shutil
import signal_disabler
import subprocess

from traceback import format_exc
from datetime import timedelta
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tenants.utils import schema_context
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import connection
from django.utils import timezone

from control.lib import get_full_url, reverse
from control.models import AccessLog, AccessCategory
from core import config
from core.elasticsearch import elasticsearch_status_report
from core.exceptions import ExceptionDuringQueryIndex, UnableToTestIndex
from core.models import SiteStat, Attachment, Entity, CommentMixin, Comment, GroupMembership, Group, Subgroup
from core.lib import ACCESS_TYPE, access_id_to_acl, get_access_id, test_elasticsearch_index
from core.models.rich_fields import ReplaceAttachments
from core.utils.export import compress_path
from core.tasks.elasticsearch_tasks import elasticsearch_delete_data_for_tenant, all_indexes
from file.models import FileFolder
from tenants.models import Client, Domain, GroupCopy, GroupCopyMapping, Agreement, AgreementVersion
from user.models import User

logger = get_task_logger(__name__)


@shared_task(bind=True, ignore_result=True)
def poll_task_result(self):
    # pylint: disable=unused-argument
    '''
    Poll task status
    '''
    from control.models import Task
    tasks = Task.objects.exclude(state__in=["SUCCESS", "FAILURE"])

    for task in tasks:
        remote_task = AsyncResult(task.task_id)
        task.state = remote_task.state

        if remote_task.successful():
            task.response = remote_task.result

        elif remote_task.failed():
            task.response = {
                "error": str(remote_task.result)
            }
        else:
            # timeout task after 1 day
            if task.created_at < (timezone.now() - timedelta(days=1)):
                task.state = "FAILURE"
                task.response = "TIMEOUT"

        if task.followup:
            task.run_followup()

        task.save()


@shared_task(bind=True)
def get_sites(self):
    # pylint: disable=unused-argument
    '''
    Used to sync sites to control
    '''
    with schema_context('public'):
        clients = Client.objects.exclude(schema_name='public')

        sites = []
        for client in clients:

            agreements_accepted = True
            for agreement in Agreement.objects.all():
                if not agreement.latest_accepted_for_tenant(client):
                    agreements_accepted = False

            sites.append({
                'id': client.id,
                'name': client.schema_name,
                'is_active': client.is_active,
                'domain': client.get_primary_domain().domain,
                'agreements_accepted': agreements_accepted
            })

        return sites


@shared_task(bind=True)
def add_site(self, schema_name, domain):
    # pylint: disable=unused-argument
    '''
    Create site from control
    '''
    with schema_context('public'):
        try:
            tenant = Client(schema_name=schema_name, name=schema_name)
            tenant.save()

            from tenants.tasks import update_post_deploy_tasks
            update_post_deploy_tasks.delay(schema_name)

            d = Domain()
            d.domain = domain
            d.tenant = tenant
            d.is_primary = True
            d.save()
        except Exception as e:
            raise Exception(e)

        return tenant.id


@shared_task(bind=True)
def delete_site(self, site_id):
    # pragma: no cover
    # pylint: disable=unused-argument
    '''
    Delete site from control
    '''
    with schema_context('public'):
        try:
            tenant = Client.objects.get(id=site_id)
            tenant.auto_drop_schema = True

            file_path = os.path.join(settings.MEDIA_ROOT, tenant.schema_name)
            schema_name = tenant.schema_name
            tenant.delete()

            # remove elasticsearch data
            elasticsearch_delete_data_for_tenant(schema_name)

            # delete files
            if os.path.exists(file_path):
                shutil.rmtree(file_path)

        except Exception as e:
            # raise general exception because remote doenst have Client exception
            raise Exception(e)

    return True


@shared_task(bind=True)
def backup_site(self, backup_site_id, skip_files=False, backup_folder=None, compress=False):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    '''
    Backup site
    '''
    with schema_context('public'):
        try:
            # does copy_site_id exist?
            backup_site = Client.objects.get(id=backup_site_id)

        except Exception as e:
            raise Exception(e)

    now = timezone.now()

    if not backup_folder:
        backup_folder = f"{now.strftime('%Y%m%d')}_{backup_site.schema_name}"

    backup_base_path = os.path.join(settings.BACKUP_PATH, backup_folder)

    # remove folder if exists
    if os.path.exists(backup_base_path):
        shutil.rmtree(backup_base_path)

    backup_data_folder = os.path.join(backup_base_path, "data")
    os.makedirs(backup_data_folder)

    # Use pg_dump to dump schema to file, removing the schema name specifics
    dump_command = (
        f'pg_dump -n {backup_site.schema_name} --host={connection.settings_dict["HOST"]} --dbname={connection.settings_dict["NAME"]} '
        f'--username={connection.settings_dict["USER"]} --no-password --schema-only --quote-all-identifiers --no-owner '
        f'| sed \'s/"{backup_site.schema_name}"\\.//g\' '
        f'| sed \'/^CREATE SCHEMA /d\' '
        f'| sed \'/^SET /d\' '
        f'| sed \'/^SELECT pg_catalog.set_config/d\' '
        f'> {backup_base_path}/schema.sql'
    )

    logger.info(dump_command)

    subprocess.run(dump_command, shell=True, env={'PGPASSWORD': connection.settings_dict["PASSWORD"]}, check=True)

    # get psycopg2 cursor
    cursor = connection.cursor()

    cursor.execute("SELECT table_name FROM information_schema.tables " +
                   "WHERE ( table_schema = %s ) " +
                   "ORDER BY table_name;", (backup_site.schema_name,))
    tables = cursor.fetchall()

    cursor.execute(f"SET search_path TO '{backup_site.schema_name}';")

    # dump data for all tables
    for row in tables:
        table = f"{row[0]}"
        file_path = f"{backup_data_folder}/{row[0]}.csv"
        with open(file_path, 'wb+') as f:
            cursor.copy_to(f, table)
        logger.info("Copy %s data to %s", table, file_path)

    # copy files
    if not skip_files:
        try:
            backup_files_folder = os.path.join(backup_base_path, "files")
            shutil.copytree(os.path.join(settings.MEDIA_ROOT, backup_site.schema_name), backup_files_folder)
        except FileNotFoundError:
            pass

    if compress:
        filename = compress_path(backup_base_path)
        if os.path.exists(filename):
            shutil.rmtree(backup_base_path, ignore_errors=True)
            return os.path.basename(filename)

    return backup_folder


@shared_task
def followup_backup_complete(backup_result, site_id, owner_guid):
    user = User.objects.get(id=owner_guid)
    backup_url = reverse('site_backup', args=[site_id])

    site = Client.objects.get(id=site_id)
    download_url = reverse('download_backup', args=[site.id, backup_result])

    AccessLog.objects.create(
        category=AccessLog.custom_category(AccessCategory.SITE_BACKUP, site_id),
        user=user,
        item_id=backup_result,
        type=AccessLog.AccessTypes.CREATE,
        site=site,
    )

    with schema_context(site.schema_name):
        context = {
            'site_name': config.NAME,
            'backup_page': get_full_url(backup_url),
            'download': download_url.endswith('.zip'),
            'download_url': get_full_url(download_url)
        }

    content = render_to_string("mail/backup_success.txt", context)

    send_mail("Site backup complete [Control2]",
              message=content,
              from_email="info@pleio.nl",
              recipient_list=[user.email],
              fail_silently=False)

    logger.warning("SENT MAIL TO %s", user.email)

    return user.email


@shared_task(bind=True)
def restore_site(self, restore_folder, schema_name, domain):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    '''
    Restore backup from path to new tenant
    '''

    backup_base_path = os.path.join(settings.BACKUP_PATH, restore_folder)

    with schema_context('public'):
        try:
            # is schema_name available ?
            if Client.objects.filter(schema_name=schema_name).first():
                raise Exception("Target schema already exists!")

            # is domain available ?
            if Domain.objects.filter(domain=domain).first():
                raise Exception("Target domain already exists!")

            # test if media folder exists
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, schema_name)):
                raise Exception("Target file path already exists, please clean up first.")

            # test if backup_folder exists
            if not os.path.exists(backup_base_path):
                raise Exception(f"Backup folder {backup_base_path} does not exist")

        except Exception as e:
            raise Exception(e)

    # get psycopg2 cursor
    cursor = connection.cursor()

    cursor.execute(f"CREATE SCHEMA \"{schema_name}\";")
    cursor.execute(f"SET search_path TO \"{schema_name}\";")

    # CREATE schema
    schema_file = open(f'{backup_base_path}/schema.sql', 'r')
    sql_create_schema = schema_file.read()

    cursor.execute(sql_create_schema)

    # temporary remove foreign key constraints
    sql_drop_key_contraints = """create table if not exists dropped_foreign_keys (
    seq bigserial primary key,
    sql text
);

do $$ declare t record;
begin
for t in select conrelid::regclass::varchar table_name, conname constraint_name,
        pg_catalog.pg_get_constraintdef(r.oid, true) constraint_definition
        from pg_catalog.pg_constraint r
        where r.contype = 'f'
        -- current schema only:
        and r.connamespace = (select n.oid from pg_namespace n where n.nspname = current_schema())
    loop

    insert into dropped_foreign_keys (sql) values (
        format('alter table %s add constraint %s %s',
            quote_ident(t.table_name), quote_ident(t.constraint_name), t.constraint_definition));

    execute format('alter table %s drop constraint %s', quote_ident(t.table_name), quote_ident(t.constraint_name));

end loop;
end $$;"""

    cursor.execute(sql_drop_key_contraints)

    restore_data_path = os.path.join(backup_base_path, "data")

    # read data from dumped tables
    for file in os.listdir(restore_data_path):
        ext = file.split(".")
        table = f"{ext[0]}"
        file_path = os.path.join(restore_data_path, file)
        f = open(file_path, 'r')

        # check if table exists
        cursor.copy_from(f, table)

        logger.info("read %s to %s", file_path, table)

    # restore foreign key constraints
    sql_restore_key_constraints = """do $$ declare t record;
begin
-- order by seq for easier troubleshooting when data does not satisfy FKs
for t in select * from dropped_foreign_keys order by seq loop
execute t.sql;
delete from dropped_foreign_keys where seq = t.seq;
end loop;
end $$;"""
    cursor.execute(sql_restore_key_constraints)

    # reset sql sequences (needed after reading data with copy_from)
    sql_reset_sql_sequences = """do $$ declare rec record;
begin
for rec in SELECT 'SELECT SETVAL(' ||quote_literal(S.relname)|| ', MAX(' ||quote_ident(C.attname)|| ') ) FROM ' ||quote_ident(T.relname)|| ';' as sql
    FROM pg_class AS S, pg_depend AS D, pg_class AS T, pg_attribute AS C, pg_tables AS PGT
    WHERE S.relkind = 'S'
        AND S.oid = D.objid
        AND D.refobjid = T.oid
        AND D.refobjid = C.attrelid
        AND D.refobjsubid = C.attnum
        AND T.relname = PGT.tablename
        AND PGT.schemaname = current_schema()
    ORDER BY S.relname loop
        execute rec.sql;
    end loop;
end $$;"""

    cursor.execute(sql_reset_sql_sequences)

    # copy files
    if os.path.exists(os.path.join(backup_base_path, "files")):
        shutil.copytree(os.path.join(backup_base_path, "files"), os.path.join(settings.MEDIA_ROOT, schema_name))

    # create new tenant if everyting is successfull
    with schema_context('public'):
        tenant = Client(schema_name=schema_name, name=schema_name)
        tenant.save()

        d = Domain()
        d.domain = domain
        d.tenant = tenant
        d.is_primary = True
        d.save()

    call_command('migrate_schemas', f'--schema={schema_name}')

    return tenant.id


@shared_task(bind=True)
def get_sites_by_email(self, email):
    # pylint: disable=unused-argument
    '''
    Get users by email
    '''
    clients = Client.objects.exclude(schema_name='public')

    data = []
    for client in clients:

        with schema_context(client.schema_name):

            user = User.objects.filter(email=email, is_active=True).first()
            if user:
                data.append({
                    'user_name': user.name,
                    'user_email': user.email,
                    'user_external_id': user.external_id,
                    'id': client.id,
                    'schema': client.schema_name,
                    'domain': client.get_primary_domain().domain
                })

    return data


@shared_task(bind=False)
def get_db_disk_usage(schema_name):
    '''
    Get db disk usage by schema_name
    '''
    with schema_context(schema_name):
        try:
            return SiteStat.objects.filter(stat_type='DB_SIZE').latest('created_at').value
        except Exception:
            return 0


@shared_task(bind=False)
def get_file_disk_usage(schema_name):
    '''
    Get file disk usage by schema_name
    '''
    with schema_context(schema_name):
        try:
            return SiteStat.objects.filter(stat_type='DISK_SIZE').latest('created_at').value
        except Exception:
            return 0


@shared_task(bind=True)
def update_site(self, site_id, data):
    # pylint: disable=unused-argument
    '''
    Update site data
    '''
    with schema_context('public'):
        try:
            tenant = Client.objects.get(id=site_id)

            if data.get('is_active', None) in [True, False]:
                tenant.is_active = data.get('is_active')

            tenant.save()

        except Exception as e:
            # raise general exception because remote doenst have Client exception
            raise Exception(e)

    return True


def get_file_field_data(source_schema_name, file_field):
    file_data = None
    with schema_context(source_schema_name):
        try:
            file_data = ContentFile(file_field.read())
            file_data.name = file_field.name
        except Exception:
            pass
    return file_data


def copy_entity_file(source_schema, target_schema, target_entity, file_attribute):
    """
    Copy a file connected to an entity
    """
    with schema_context(source_schema):
        source_file = getattr(target_entity, file_attribute)

    if source_file:
        file_contents = get_file_field_data(source_schema, source_file.upload)

        with schema_context(target_schema):
            target_file = FileFolder.objects.create(
                owner=target_entity.owner,
                upload=file_contents,
                read_access=[ACCESS_TYPE.public],
                write_access=[ACCESS_TYPE.user.format(target_entity.owner.id)]
            )

        setattr(target_entity, file_attribute, target_file)


def copy_attachments(source_schema, target_schema, target_entity):
    """
    Copy entity attachments and replace rich_field links
    """
    with schema_context(source_schema):
        attachments = Attachment.objects.filter(pk__in=[item for item in target_entity.lookup_attachments()])

    attachment_map = ReplaceAttachments()
    for attachment in attachments:
        attachment_contents = get_file_field_data(source_schema, attachment.upload)

        with schema_context(target_schema):
            new_attachment = Attachment()
            new_attachment.upload = attachment_contents
            new_attachment.owner = target_entity.owner
            new_attachment.save()
            logger.info("saved new attachemnt %s", str(new_attachment.id))

        attachment_map.append(str(attachment.id), str(new_attachment.id))

    if hasattr(target_entity, 'replace_attachments'):
        target_entity.replace_attachments(attachment_map)


def get_or_create_user(copy, source_user_id):
    created = False
    with schema_context(copy.source_tenant):
        source_user = User.objects.with_deleted().get(id=source_user_id)

    with schema_context(copy.target_tenant):
        user = User.objects.with_deleted().filter(email__iexact=source_user.email).first()

        if not user:
            with signal_disabler.disable():  # prevent auto join in groups
                user = User.objects.create(
                    name=source_user.name,
                    email=source_user.email,
                    picture=source_user.picture,
                    external_id=source_user.external_id,
                    is_active=source_user.is_active,
                    ban_reason=source_user.ban_reason
                )
            created = True

    with schema_context('public'):
        GroupCopyMapping.objects.get_or_create(
            copy=copy,
            entity_type='User',
            source_id=source_user.id,
            target_id=user.id,
            created=created
        )

    return user


@shared_task(bind=False)
def copy_group_to_tenant(source_schema, action_user_id, group_id, target_schema):
    # pylint: disable=too-many-locals
    '''
    Copy group from one tenant to another
    '''
    now = timezone.now()

    copy = GroupCopy.objects.create(
        source_tenant=source_schema,
        target_tenant=target_schema,
        source_id=group_id,
        task_id=copy_group_to_tenant.request.id
    )

    copy.task_id = copy_group_to_tenant.request.id
    copy.save()

    with schema_context(source_schema):
        action_user = User.objects.get(id=action_user_id)
        group = Group.objects.get(id=group_id)

    with schema_context(target_schema):
        target_group = group
        target_group.owner = get_or_create_user(copy, group.owner_id)
        target_group.created_at = now
        target_group.updated_at = now
        target_group.is_featured = False

        copy_entity_file(source_schema, target_schema, target_group, "featured_image")
        copy_entity_file(source_schema, target_schema, target_group, "icon")

        target_group.pk = None
        target_group.id = None

        copy_attachments(source_schema, target_schema, target_group)

        target_group.save()

    copy.action_user_id = action_user.id
    copy.target_id = target_group.id
    copy.save()

    logger.info("Created group %s", target_group)

    with schema_context(copy.source_tenant):
        subgroups = list(item for item in Subgroup.objects.filter(group__id=copy.source_id).all())

    with schema_context(copy.target_tenant):
        target_group = Group.objects.get(id=copy.target_id)

        for s in subgroups:
            subgroup_source_id = s.id
            s.group = target_group
            s.pk = None
            s.id = None
            s.save()

            GroupCopyMapping.objects.create(
                copy=copy,
                entity_type='Subgroup',
                source_id=subgroup_source_id,
                target_id=s.id
            )

    logger.info("Added %i subgroups", len(subgroups))

    return copy_group_memberships(copy.id)


@shared_task(bind=False)
def copy_file_from_source_tenant(source_schema, target_schema, dst_file):
    '''
    Separate load heavy task to copy file from source tenant to target in group copy
    '''
    src_file = dst_file.replace(os.path.join(settings.MEDIA_ROOT, target_schema), os.path.join(settings.MEDIA_ROOT, source_schema))

    if os.path.isfile(src_file):
        dst_folder = os.path.dirname(dst_file)
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        shutil.copy(src_file, dst_file)


def copy_group_memberships(copy_id):
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    '''
    Copy group users from one tenant to another
    '''
    with schema_context("public"):
        copy = GroupCopy.objects.get(id=copy_id)

    with schema_context(copy.source_tenant):
        memberships = list(item for item in GroupMembership.objects.filter(group__id=copy.source_id).all())

    with schema_context(copy.target_tenant):
        target_group = Group.objects.get(id=copy.target_id)

        for m in memberships:
            m.user = get_or_create_user(copy, m.user_id)
            m.group = target_group
            m.pk = None
            m.id = None
            m.save()

    logger.info("Inserted %i group members", len(memberships))

    # loop over all members and set subgroup memberships
    subgroup_memberships = []
    with schema_context(copy.source_tenant):
        for subgroup in Subgroup.objects.filter(group__id=copy.source_id).all():
            for member in subgroup.members.all():
                subgroup_memberships.append({'subgroup_id': subgroup.id, 'user_id': member.id})

    with schema_context(copy.target_tenant):
        target_group = Group.objects.get(id=copy.target_id)
        for membership in subgroup_memberships:
            subgroup_id = GroupCopyMapping.objects.get(
                copy=copy,
                entity_type='Subgroup',
                source_id=membership.get('subgroup_id')
            ).target_id

            subgroup = Subgroup.objects.get(id=subgroup_id)
            user = get_or_create_user(copy, membership.get('user_id'))
            subgroup.members.add(user)

    logger.info("Added %i subgroup members", len(subgroup_memberships))

    return copy_group_entities(copy.id)


def copy_group_entities(copy_id):
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    '''
    Copy entities in group from one tenant to another
    '''

    with schema_context("public"):
        copy = GroupCopy.objects.get(id=copy_id)

    def transform_acl_to_access_id(acl):
        access_id = get_access_id(acl)

        if access_id > 10000:
            old_subgroup_id = access_id - 10000
            subgroup_map = GroupCopyMapping.objects.filter(
                copy=copy,
                entity_type='Subgroup',
                source_id=old_subgroup_id
            ).first()

            if subgroup_map:
                access_id = subgroup_map.target_id.int + 10000
            else:
                access_id = 0

        return access_id

    with schema_context(copy.source_tenant):
        entities = list(item for item in Entity.objects.filter(group__id=copy.source_id).select_subclasses())

    with schema_context(copy.target_tenant):
        target_group = Group.objects.get(id=copy.target_id)

        connect_parent = []
        connect_best_answers = []
        connect_sub_comments = []
        connect_best_answers = []

        for target_entity in entities:
            source_entity_id = target_entity.id
            parent_source_id = None
            best_answer_source_id = None
            comments = []
            event_attendees = []

            if target_entity.__class__.__name__ in ["Blog", "StatusUpdate", "Task", "FileFolder", "Wiki", "Event", "Question", "Discussion"]:

                # default entity stuff
                target_entity.group = target_group
                target_entity.owner = get_or_create_user(copy, target_entity.owner_id)
                target_entity.is_featured = False
                target_entity.notifications_created = True
                target_entity.read_access = access_id_to_acl(target_entity, transform_acl_to_access_id(target_entity.read_access))
                target_entity.write_access = access_id_to_acl(target_entity, transform_acl_to_access_id(target_entity.write_access))

                # specific entity type stuff
                if target_entity.__class__.__name__ in ["Blog", "Wiki", "Event"]:
                    copy_entity_file(copy.source_tenant, copy.target_tenant, target_entity, "featured_image")

                if target_entity.__class__.__name__ in ["Blog", "StatusUpdate", "Task", "Wiki", "Event"]:
                    copy_attachments(copy.source_tenant, copy.target_tenant, target_entity)

                if target_entity.__class__.__name__ in ["FileFolder", "Wiki", "Event"]:
                    with schema_context(copy.source_tenant):
                        if target_entity.parent:
                            parent_source_id = target_entity.parent.id
                            target_entity.parent = None

                if target_entity.__class__.__name__ in ["FileFolder"]:
                    if target_entity.upload:
                        copy_file_from_source_tenant.delay(copy.source_tenant, copy.target_tenant, target_entity.upload.path)
                    if target_entity.thumbnail:
                        copy_file_from_source_tenant.delay(copy.source_tenant, copy.target_tenant, target_entity.thumbnail.path)

                if target_entity.__class__.__name__ in ["Question"]:
                    with schema_context(copy.source_tenant):
                        if target_entity.best_answer:
                            best_answer_source_id = target_entity.best_answer.id
                            target_entity.best_answer = None

                if target_entity.__class__.__name__ in ["Event"]:
                    with schema_context(copy.source_tenant):
                        event_attendees = list(item for item in target_entity.attendees.all())

                if target_entity.__class__ in CommentMixin.__subclasses__():
                    with schema_context(copy.source_tenant):
                        comments = list(target_entity.get_flat_comment_list())

                target_entity.pk = None
                target_entity.id = None

                with signal_disabler.disable():
                    target_entity.save()

                GroupCopyMapping.objects.create(
                    copy=copy,
                    entity_type=target_entity.__class__.__name__,
                    source_id=source_entity_id,
                    target_id=target_entity.id
                )

                if parent_source_id:
                    connect_parent.append({'entity_id': target_entity.id, 'parent_source_id': parent_source_id})

                if best_answer_source_id:
                    connect_best_answers.append({'entity_id': target_entity.id, 'best_answer_source_id': best_answer_source_id})

                for comment in comments:
                    container_source_id = None
                    comment_source_id = comment.id
                    comment.owner = get_or_create_user(copy, comment.owner_id)
                    copy_attachments(copy.source_tenant, copy.target_tenant, comment)
                    comment.pk = None
                    comment.id = None
                    with schema_context(copy.source_tenant):
                        if comment.container:
                            if comment.container.__class__.__name__ == 'Comment':  # is subcomment, for now set container to target_entity
                                container_source_id = comment.container.id

                    comment.container = target_entity

                    with signal_disabler.disable():
                        comment.save()

                    if container_source_id:
                        connect_sub_comments.append({'comment_id': comment.id, 'container_source_id': container_source_id})

                    GroupCopyMapping.objects.create(
                        copy=copy,
                        entity_type=comment.__class__.__name__,
                        source_id=comment_source_id,
                        target_id=comment.id
                    )

                # add event attendees
                for attendee in event_attendees:
                    attendee.event = target_entity
                    attendee.user = get_or_create_user(copy, attendee.user_id)
                    attendee.pk = None
                    attendee.id = None
                    attendee.save()

        logger.info("Inserted %i entities", len(entities))

        # rebuild parent/child relations
        for connect in connect_parent:
            entity = Entity.objects.get_subclass(id=connect.get('entity_id'))
            parent_id = GroupCopyMapping.objects.get(
                copy=copy,
                entity_type=entity.__class__.__name__,
                source_id=connect.get('parent_source_id')
            ).target_id
            parent = Entity.objects.get_subclass(id=parent_id)
            if parent != entity:
                entity.parent = parent
            with signal_disabler.disable():
                entity.save()

        # rebuild subcomment container relations
        for connect in connect_sub_comments:
            comment = Comment.objects.get(id=connect.get('comment_id'))
            container_id = GroupCopyMapping.objects.get(
                copy=copy,
                entity_type=comment.__class__.__name__,
                source_id=connect.get('container_source_id')
            ).target_id
            container = Comment.objects.get(id=container_id)
            comment.container = container
            with signal_disabler.disable():
                comment.save()

        # connect best anwswer
        for connect in connect_best_answers:
            entity = Entity.objects.get_subclass(id=connect.get('entity_id'))
            comment_id = GroupCopyMapping.objects.get(
                copy=copy,
                entity_type='Comment',
                source_id=connect.get('best_answer_source_id')
            ).target_id
            answer = Comment.objects.get(id=comment_id)
            entity.best_answer = answer
            entity.save()

    logger.info("Rebuild %i relations", len(connect_parent) + len(connect_sub_comments) + len(connect_best_answers))

    return copy.id


@shared_task(bind=True)
def get_agreements(self):
    # pylint: disable=unused-argument
    '''
    Get agreements
    '''
    result = []

    with schema_context('public'):
        agreements = Agreement.objects.all()
        for agreement in agreements:
            result.append({
                'id': agreement.id,
                'name': agreement.name,
                'versions': [{
                    'id': version.id,
                    'version': version.version,
                    'document': version.get_absolute_url(),
                    'created_at': version.created_at
                } for version in agreement.versions.all()]
            })

    return result


@shared_task(bind=True)
def add_agreement(self, name):
    # pylint: disable=unused-argument
    agreement = Agreement.objects.create(
        name=name
    )

    return {
        'id': agreement.id,
        'name': agreement.name
    }


@shared_task(bind=True)
def add_agreement_version(self, agreement_id, version, document_path):
    # pylint: disable=unused-argument
    with schema_context('public'):
        agreement = Agreement.objects.get(id=agreement_id)

        fd = open(document_path, "rb")

        save_as = ContentFile(fd.read())
        save_as.name = os.path.basename(fd.name)

        version = AgreementVersion.objects.create(
            agreement=agreement,
            version=version,
            document=save_as
        )

    return {
        'id': version.id,
        'version': version.version,
        'document': version.get_absolute_url()
    }


@shared_task
def update_elasticsearch_status():
    for client in Client.objects.exclude(schema_name='public'):
        update_elasticsearch_status_for_tenant.delay(client.id)


@shared_task
def update_elasticsearch_status_for_tenant(client_id):
    # pylint: disable=protected-access
    client = Client.objects.get(id=client_id)
    with schema_context(client.schema_name):
        try:
            index_test_result = []
            for index in all_indexes():
                try:
                    test_elasticsearch_index(index._name)
                except ExceptionDuringQueryIndex as e:
                    index_test_result.append({'index': index._name,
                                              "message": str(e)})
                except UnableToTestIndex:
                    index_test_result.append({'index': index._name,
                                              "message": "unable to test %s" % index._name})
            access_result = {
                "result": index_test_result,
            }
        except Exception as e:
            access_result = {
                "exception": str(e.__class__),
                "message": str(e),
                "backtrace": format_exc()
            }
        try:
            index_status_result = {
                "result": elasticsearch_status_report(alert_only=True)
            }
        except Exception as e:
            index_status_result = {"exception": e.__class__,
                                   "message": str(e),
                                   "backtrace": format_exc()}

    from control.models import ElasticsearchStatus
    ElasticsearchStatus.objects.cleanup(client=client)
    ElasticsearchStatus.objects.create(client=client,
                                       index_status=index_status_result,
                                       access_status=access_result)
