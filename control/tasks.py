from __future__ import absolute_import, unicode_literals

import os
import tempfile
import shutil
from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger

from tenants.models import Client, Domain
from django_tenants.utils import schema_context
from django.conf import settings
from django.db import connection
from user.models import User

logger = get_task_logger(__name__)

@shared_task(bind=True)
def get_sites(self):
    # pylint: disable=unused-argument
    '''
    Used to sync sites to control
    '''
    clients = Client.objects.exclude(schema_name='public')

    sites = []
    for client in clients:
        sites.append({
            'id': client.id,
            'name': client.schema_name,
            'domain': client.get_primary_domain().domain
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
    # pylint: disable=unused-argument
    '''
    Delete site from control
    '''
    with schema_context('public'):
        try:
            tenant = Client.objects.get(id=site_id)
            tenant.auto_drop_schema = True

            file_path = os.path.join(settings.MEDIA_ROOT, tenant.schema_name)
            tenant.delete()

            # delete files
            if os.path.exists(file_path):
                shutil.rmtree(file_path)

        except Exception as e:
            # raise general exception because remote doenst have Client exception
            raise Exception(e)

    return True

@shared_task(bind=True)
def get_sites_admin(self):
    # pylint: disable=unused-argument
    '''
    Get all site administrators
    '''
    clients = Client.objects.exclude(schema_name='public')

    admins = []
    for client in clients:

        with schema_context(client.schema_name):

            users = User.objects.filter(roles__contains=['ADMIN'], is_active=True)
            for user in users:
                admins.append({
                    'name': user.name,
                    'email': user.email,
                    'client_id': client.id,
                    'client_domain': client.get_primary_domain().domain
                })

    return admins

@shared_task(bind=True)
def copy_site(self, copy_site_id, schema_name, domain):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-locals
    '''
    Copy site to new schema
    '''
    with schema_context('public'):
        try:
            # does copy_site_id exist?
            copy_site = Client.objects.get(id=copy_site_id)

            # is schema_name available ?
            if Client.objects.filter(schema_name=schema_name).first():
                raise Exception("Target schema already exists!")

            # is domain available ?
            if Domain.objects.filter(domain=domain).first():
                raise Exception("Target domain already exists!")

            # test if media folder exists
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, schema_name)):
                raise Exception("Target file path already exists, please clean up first.")

        except Exception as e:
            raise Exception(e)

    export_folder = os.path.join(tempfile.gettempdir(), f"dump_{copy_site.schema_name}")

    # remove folder if exists
    if os.path.exists(export_folder):
        shutil.rmtree(export_folder)

    os.makedirs(export_folder)

    skip_tables = ("auth_permission", "django_content_type", "django_migrations", "django_session")

    with connection.connection.cursor() as cursor:
        cursor.execute( "SELECT table_name FROM information_schema.tables " +
                        "WHERE ( table_schema = %s AND table_name NOT IN %s ) " +
                        "ORDER BY table_name;", (copy_site.schema_name, skip_tables))
        tables = cursor.fetchall()

    # dump data for all tables
    for row in tables:
        table = f"{copy_site.schema_name}.{row[0]}"
        file_path = f"{export_folder}/{row[0]}.csv"
        f = open(file_path, 'wb+')

        with connection.connection.cursor() as cursor:
            cursor.copy_to(f, table)
        logger.info("Copy %s data to %s", table, file_path)

    # create new tenant
    with schema_context('public'):
        tenant = Client(schema_name=schema_name, name=schema_name)
        tenant.save()

        d = Domain()
        d.domain = domain
        d.tenant = tenant
        d.is_primary = True
        d.save()

    # get psycopg2 cursor
    cursor = connection.connection.cursor()

    cursor.execute(f"SET search_path TO {tenant.schema_name};")

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

    # read data from dumped tables
    for row in tables:

        table = f"{tenant.schema_name}.{row[0]}"
        file_path = f"{export_folder}/{row[0]}.csv"
        f = open(file_path, 'r')

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
    if os.path.exists(os.path.join(settings.MEDIA_ROOT, copy_site.schema_name)):
        shutil.copytree(os.path.join(settings.MEDIA_ROOT, copy_site.schema_name), os.path.join(settings.MEDIA_ROOT, tenant.schema_name))

    # cleanup dump folder
    shutil.rmtree(export_folder, ignore_errors=True)

    return tenant.id

@shared_task(bind=True)
def backup_site(self, backup_site_id):
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

    now = datetime.now()
    backup_folder = f"{now.strftime('%Y%m%d')}_{backup_site.schema_name}"
    backup_base_path = os.path.join(settings.BACKUP_PATH, backup_folder)

    # remove folder if exists
    if os.path.exists(backup_base_path):
        shutil.rmtree(backup_base_path)

    backup_schema_folder = os.path.join(backup_base_path, "schema")
    os.makedirs(backup_schema_folder)

    skip_tables = ("auth_permission", "django_content_type", "django_migrations", "django_session", "django_admin_log")

    # get psycopg2 cursor
    cursor = connection.connection.cursor()

    cursor.execute( "SELECT table_name FROM information_schema.tables " +
                    "WHERE ( table_schema = %s AND table_name NOT IN %s ) " +
                    "ORDER BY table_name;", (backup_site.schema_name, skip_tables))
    tables = cursor.fetchall()

    cursor.execute(f"SET search_path TO {backup_site.schema_name};")

    # dump data for all tables
    for row in tables:
        table = f"{row[0]}"
        file_path = f"{backup_schema_folder}/{row[0]}.csv"
        f = open(file_path, 'wb+')

        cursor.copy_to(f, table)
        logger.info("Copy %s data to %s", table, file_path)

    # copy files
    backup_files_folder = os.path.join(backup_base_path, "files")
    shutil.copytree(os.path.join(settings.MEDIA_ROOT, backup_site.schema_name), backup_files_folder)

    return backup_folder

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

    # create new tenant
    with schema_context('public'):
        tenant = Client(schema_name=schema_name, name=schema_name)
        tenant.save()

        d = Domain()
        d.domain = domain
        d.tenant = tenant
        d.is_primary = True
        d.save()

    # get psycopg2 cursor
    cursor = connection.connection.cursor()

    cursor.execute(f"SET search_path TO {tenant.schema_name};")

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

    restore_schema_path = os.path.join(backup_base_path, "schema")

    # read data from dumped tables
    for file in os.listdir(restore_schema_path):
        ext = file.split(".")
        table = f"{tenant.schema_name}.{ext[0]}"
        file_path = os.path.join(restore_schema_path, file)
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
        shutil.copytree(os.path.join(backup_base_path, "files"), os.path.join(settings.MEDIA_ROOT, tenant.schema_name))

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