import os
import re
import tempfile
import logging
import textract
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import FileFolder
from core.documents import DefaultDocument, ngram_analyzer

logger = logging.getLogger(__name__)

@registry.register_document
class FileDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    title = fields.TextField(
        analyzer=ngram_analyzer
    )
    file_contents = fields.ListField(fields.TextField())

    def prepare_file_contents(self, instance):
        # pylint: disable=unused-argument
        file_contents = ''
        try:
            # copy file to temp folder to process
            if not instance.is_folder and instance.upload:
                extension = os.path.splitext(instance.upload.name)[1]
                if extension in ['.pdf', '.doc', '.docx', '.pptx', '.txt']:
                    with instance.upload.open() as f:
                        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp:
                            for line in f:
                                temp.write(line)
                            temp.close()
                            file_contents = re.findall(r"[\w']+", str(textract.process(temp.name, encoding='utf8')))
                            os.unlink(temp.name)

            return file_contents
        except Exception as e:
            logger.error('Error occured while indexing file (%s): %s', instance.id, e)
            return file_contents

    class Index:
        name = 'entities'

    class Django:
        model = FileFolder

        fields = [
            'created_at',
            'updated_at'
        ]
