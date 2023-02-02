from post_deploy import post_deploy_action

from core.lib import is_schema_public


@post_deploy_action
def remove_external_content_index():
    # execute once
    if not is_schema_public():
        return

    # pylint: disable=unexpected-keyword-arg
    from elasticsearch import Elasticsearch
    es = Elasticsearch()
    es.indices.delete(index='external_content', ignore=[400, 404])
