from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

from core.lib import NumberIncrement


class Tag(models.Model):
    label = models.CharField(max_length=256, unique=True)

    @staticmethod
    def translate_tags(tags):
        synonym_to_tag = {s.label.lower(): s.tag.label.lower() for s in TagSynonym.objects.all()}
        for tag in tags:
            ltag = tag.lower()
            try:
                yield synonym_to_tag[ltag]
            except KeyError:
                yield ltag

    @property
    def all_matches(self):
        yield self.label
        for s in self.synonyms.all():
            yield s.label

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['label']


class TagSynonym(models.Model):
    label = models.CharField(max_length=256, unique=True, primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="synonyms")

    def __str__(self):
        return "%s (%s)" % (self.label, self.tag.label)

    class Meta:
        ordering = ['label']


class EntityTag(models.Model):
    tag = models.ForeignKey('core.Tag',
                            on_delete=models.CASCADE)
    entity_id = models.UUIDField()
    author_label = models.CharField(max_length=256)
    weight = models.IntegerField(default=0)

    @classmethod
    def summary(cls, entity_id):
        return [et.tag.label for et in cls.objects.filter(entity_id=entity_id)]

    def __str__(self):
        return "%s (%s)" % (self.author_label, self.tag.label)

    @property
    def entity(self):
        for m in _model_repository:
            try:
                return m.objects.get(id=self.entity_id)
            except m.DoesNotExist:
                pass
        return None

    class Meta:
        ordering = ['weight']


_model_repository = set()


class TagsModel(models.Model):
    """
    Classes that include this mixin should:

    1. Also define a _tag_summary ArrayField.
    2. Also register itself in the ready method of the app using register_model_for_tags().
    """

    class Meta:
        abstract = True

    _tag_summary = ArrayField(models.CharField(max_length=256),
                              blank=True, default=list,
                              db_column='tags')
    _category_summary = ArrayField(models.CharField(max_length=256),
                                   blank=True, default=list,
                                   db_column='categories')

    category_tags = models.JSONField(default=list, blank=True)

    @property
    def tags(self):
        my_tags = EntityTag.objects.filter(entity_id=self.id)
        return [ref.author_label for ref in my_tags]

    @property
    def tags_matches(self):
        my_tags = EntityTag.objects.filter(entity_id=self.id)
        result = []
        for entity_tag in my_tags:
            result.extend(entity_tag.tag.all_matches)
        for category in self.category_tags:
            result.extend(flat_category_tags(category, brief=True))
        return result

    @tags.setter
    def tags(self, tags):
        expected = []
        tag_mapping = dict()
        for tag in tags:
            tag_obj = Tag.objects.filter(Q(label=tag.lower()) | Q(synonyms__label=tag.lower())).first()
            if not tag_obj:
                tag_obj = Tag.objects.create(label=tag.lower())
            expected.append(tag_obj)
            if not tag_mapping.get(tag_obj.label):
                tag_mapping[tag_obj.label] = tag

        expected_labels = {tag.label for tag in expected}
        for label in self.tags:
            if label not in expected_labels:
                try:
                    remove = EntityTag.objects.get(tag__label=label.lower(), entity_id=self.id)
                    remove.delete()
                except EntityTag.DoesNotExist:
                    pass

        weight = NumberIncrement()
        for tag_obj in expected:
            obj, _ = EntityTag.objects.get_or_create(tag=tag_obj,
                                                     entity_id=self.id)
            obj.author_label = tag_mapping[tag_obj.label]
            obj.weight = weight.next()
            obj.save()

        self._expected_labels = expected_labels

    @property
    def category_tags_index(self):
        for category in self.category_tags:
            yield from flat_category_tags(category)


def flat_category_tags(category, brief=False):
    for value in category['values']:
        if brief:
            yield value.lower()
        else:
            yield f"{value} ({category['name']})".lower()


def register_model_for_tags(cls):
    """
    Register classes that implement TagsModel in the ready function of the app.
    """
    _model_repository.add(cls)


def is_registered_for_tags(cls):
    compare = set(cls.__bases__)
    compare.add(cls)

    return len(compare & _model_repository) > 0


@receiver(pre_save)
def pre_save_entity(sender, instance, **kwargs):
    # pylint: disable=protected-access
    # pylint: disable=unused-argument
    if isinstance(instance, TagsModel):
        assert is_registered_for_tags(instance.__class__), \
            "Register the base TagsModel model using register_model_for_tags at the app's ready method."
        assert '_tag_summary' in [f.name for f in instance._meta.fields], "Provide a _tag_summary ArrayField"
        instance._tag_summary = EntityTag.summary(instance.id)
        instance._category_summary = [t for t in instance.category_tags_index]


@receiver(post_delete)
def post_delete_entity(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    if isinstance(instance, TagsModel):
        EntityTag.objects.filter(entity_id=instance.id).delete()
