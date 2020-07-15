from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Blog
from core.documents import DefaultDocument
from elasticsearch_dsl import analysis, analyzer, tokenizer


custom_stop_filter = analysis.token_filter(
    "custom_stop_filter",
    type="stop",
    stopwords=['_dutch_'],
    ignore_case=True
)


ngram_analyzer = analyzer(
    'ngram_analyzer',
    tokenizer=tokenizer(
        'description_ngram',
        type='ngram',
        min_gram=3,
        max_gram=3,
        token_chars=["letter", "digit", "punctuation", "symbol"]
    ),
    filter=['lowercase', custom_stop_filter]
)


@registry.register_document
class BlogDocument(DefaultDocument):
    id = fields.TextField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    description = fields.TextField(
        analyzer=ngram_analyzer
    )

    class Index:
        name = 'entities'

    class Django:
        model = Blog

        fields = [
            'title',
            'created_at',
            'updated_at'
        ]
