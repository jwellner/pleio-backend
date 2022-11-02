import os
import re
import tempfile
import logging
import textract
from django.db import models
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import FileFolder
from core.documents import DefaultDocument, custom_analyzer
from core.utils.convert import tiptap_to_text


logger = logging.getLogger(__name__)


@registry.register_document
class FileDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
    tags_matches = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
    category_tags = fields.ListField(fields.KeywordField(attr='category_tags_index'))

    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    title = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard",
        boost=2,
        fields={'raw': fields.KeywordField()}
    )
    file_contents = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard"
    )

    read_access_weight = fields.IntegerField()

    description = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard"
    )

    def prepare_file_contents(self, instance):
        # pylint: disable=unused-argument
        file_contents = ''
        try:
            # copy file to temp folder to process
            if instance.type == FileFolder.Types.FILE and instance.upload:
                extension = os.path.splitext(instance.upload.name)[1]
                if extension in ['.pdf', '.doc', '.docx', '.pptx', '.txt']:
                    with instance.upload.open() as f:
                        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp:
                            for line in f:
                                temp.write(line)
                            temp.close()
                            file_contents = re.sub(r"\s+", " ",
                                                   textract.process(temp.name, encoding='utf8').decode("utf-8"))
                            os.unlink(temp.name)

            return file_contents
        except Exception as e:
            logger.error('Error occured while indexing file (%s): %s', instance.id, e)
            return file_contents

    def prepare_tags(self, instance):
        return [x.lower() for x in instance.tags]

    def prepare_description(self, instance):
        return tiptap_to_text(instance.rich_description)

    def update(self, thing, refresh=None, action='index', parallel=False, **kwargs):
        if isinstance(thing, models.Model) and not thing.group and action == "index":
            action = "delete"
            kwargs = {**kwargs, 'raise_on_error': False}
        return super(FileDocument, self).update(thing, refresh, action, **kwargs)

    def get_queryset(self):
        queryset = super(FileDocument, self).get_queryset()
        return queryset.exclude(group=None)

    def should_index_object(self, obj):
        return bool(obj.group)

    class Index:
        name = 'file'

    class Django:
        model = FileFolder

        fields = [
            'created_at',
            'updated_at',
            'published'
        ]
