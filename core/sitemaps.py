from django.contrib import sitemaps
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

from core import config
from core.models import Entity

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        if config.ENABLE_SEARCH_ENGINE_INDEXING:
            return ['/']
        return []

    def location(self, item):
        # pylint: disable=arguments-differ
        return item

class PublicEntities(sitemaps.Sitemap):
    priority = 0.5

    def items(self):
        if config.ENABLE_SEARCH_ENGINE_INDEXING:
            anonymousUser = AnonymousUser()
            subtype_filter = Q()
            subtype_filter.add(~Q(wiki__isnull = True), Q.OR)
            subtype_filter.add(~Q(page__isnull = True), Q.OR)
            subtype_filter.add(~Q(news__isnull = True), Q.OR)
            subtype_filter.add(~Q(blog__isnull = True), Q.OR)
            subtype_filter.add(~Q(event__isnull = True), Q.OR)
            subtype_filter.add(~Q(discussion__isnull = True), Q.OR)
            subtype_filter.add(~Q(question__isnull = True), Q.OR)

            return Entity.objects.visible(anonymousUser).filter(subtype_filter).select_subclasses()[0:2000]
        return []

    def location(self, item):
        # pylint: disable=arguments-differ
        return item.url

    def lastmod(self, item):
        return item.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "public": PublicEntities
}
