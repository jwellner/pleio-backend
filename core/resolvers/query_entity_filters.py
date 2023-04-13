from django.db.models import Q

from external_content.utils import is_external_content_source


class EntityFilterBase:
    key = None

    def add_if_applicable(self, query, subtypes):
        if not subtypes or self.key in subtypes:
            self.add(query)

    def add(self, query):
        raise NotImplementedError()


class NewsEntityFilter(EntityFilterBase):
    key = 'news'

    def add(self, query):
        query.add(~Q(news__isnull=True), Q.OR)


class BlogEntityFilter(EntityFilterBase):
    key = 'blog'

    def add(self, query):
        query.add(~Q(blog__isnull=True), Q.OR)


class EventEntityFilter(EntityFilterBase):
    key = "event"

    def add_if_applicable(self, query, subtypes):
        if subtypes == ['event']:
            self.add_all_events(query)
        else:
            super().add_if_applicable(query, subtypes)

    @staticmethod
    def add_all_events(query):
        query.add(~Q(event__isnull=True)
                  & ~Q(event__parent__isnull=False), Q.OR)

    def add(self, query):
        query.add(~Q(event__isnull=True)
                  & ~Q(event__parent__isnull=False)
                  & Q(event__index_item=True), Q.OR)


class DiscussionEntityFilter(EntityFilterBase):
    key = "discussion"

    def add(self, query):
        query.add(~Q(discussion__isnull=True), Q.OR)


class StatusupdateEntityFilter(EntityFilterBase):
    key = "statusupdate"

    def add(self, query):
        query.add(~Q(statusupdate__isnull=True), Q.OR)


class QuestionEntityFilter(EntityFilterBase):
    key = "question"

    def add(self, query):
        query.add(~Q(question__isnull=True), Q.OR)


class PollEntityFilter(EntityFilterBase):
    key = "poll"

    def add(self, query):
        query.add(~Q(poll__isnull=True), Q.OR)


class WikiEntityFilter(EntityFilterBase):
    key = "wiki"

    def add(self, query):
        query.add(~Q(wiki__isnull=True), Q.OR)


class PageEntityFilter(EntityFilterBase):
    key = "page"

    def add(self, query):
        query.add(~Q(page__isnull=True), Q.OR)


class FileEntityFilter(EntityFilterBase):
    key = "file"

    def add(self, query):
        query.add(~Q(filefolder__isnull=True) & Q(filefolder__type='File'), Q.OR)


class FolderEntityFilter(EntityFilterBase):
    key = "folder"

    def add(self, query):
        query.add(~Q(filefolder__isnull=True) & Q(filefolder__type='Folder'), Q.OR)


class PadEntityFilter(EntityFilterBase):
    key = "pad"

    def add(self, query):
        query.add(~Q(filefolder__isnull=True) & Q(filefolder__type='Pad'), Q.OR)


class TaskEntityFilter(EntityFilterBase):
    key = "task"

    def add(self, query):
        query.add(~Q(task__isnull=True), Q.OR)


class ExternalcontentEntityFilter(EntityFilterBase):

    def add_if_applicable(self, query, subtypes):
        if subtypes:
            self.add_matching(query, subtypes)
        else:
            self.add(query)

    @staticmethod
    def add_matching(query, subtypes):
        for object_type in subtypes:
            if is_external_content_source(object_type):
                query.add(~Q(externalcontent__isnull=True) & Q(externalcontent__source_id=object_type), Q.OR)

    def add(self, query):
        query.add(~Q(externalcontent__isnull=True), Q.OR)
