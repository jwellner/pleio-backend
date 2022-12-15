import csv
import os
import zipfile

from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.db import models

from core.lib import datetime_isoformat


def compress_path(path):
    target_path = os.path.join(os.path.dirname(path), os.path.basename(path) + '.zip')

    zip_file = zipfile.ZipFile(target_path, mode='w', compression=zipfile.ZIP_DEFLATED)
    add_to_zip_recursive(path, '', zip_file)
    zip_file.close()

    return target_path


def add_to_zip_recursive(root, path, zip_file):
    try:
        for filename in os.listdir(os.path.join(root, path)):
            add_to_zip_recursive(root=root,
                                 path=os.path.join(path, filename),
                                 zip_file=zip_file)
    except NotADirectoryError:
        if path == '':
            zip_file.write(root, arcname=os.path.basename(root))
        else:
            zip_file.write(os.path.join(root, path), arcname=path)


def stream(items, pseudo_buffer, domain, Model=None):
    # pylint: disable=unidiomatic-typecheck
    fields = []
    field_names = []
    for field in Model._meta.get_fields():
        if (
                type(field) in [models.OneToOneRel, models.ForeignKey, models.ManyToOneRel, GenericRelation, GenericForeignKey]
                and not (field.name == 'owner')
        ):
            continue
        fields.append(field)
        field_names.append(field.name)

    # if more fields needed, refactor
    field_names.append('url')
    field_names.append('owner_url')

    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    yield writer.writerow(field_names)

    def get_data(entity, fields):
        field_values = []
        for field in fields:
            field_value = field.value_from_object(entity)
            if field.get_internal_type() == 'DateTimeField':
                try:
                    field_value = datetime_isoformat(field_value)
                except Exception:
                    pass
            field_values.append(field_value)

        # if more fields needed, refactor

        url = entity.url if hasattr(entity, 'url') else ''
        field_values.append(f"https://{domain}{url}")

        owner_url = f"{entity.owner.url}" if hasattr(entity, 'owner') else ''
        field_values.append(f"https://{domain}{owner_url}")

        return field_values

    for item in items:
        yield writer.writerow(get_data(item, fields))
