from collections import defaultdict

from django.core.exceptions import ValidationError


class WidgetSerializerBase:
    def serialize(self):
        raise NotImplementedError()

    def attachments(self):
        raise NotImplementedError()

    def rich_fields(self):
        raise NotImplementedError()


class WidgetSerializer(WidgetSerializerBase):
    def __init__(self, widget, acting_user=None):
        self.widget = widget
        self.acting_user = acting_user

    @property
    def type(self):
        return self.widget.get('type')

    @property
    def settings(self):
        return [WidgetSettingSerializer(s, self.acting_user) for s in self.widget.get('settings', []) or []]

    def serialize(self):
        result = defaultdict(list)
        result['type'] = self.type
        for setting in self.settings:
            result['settings'].append(setting.serialize())
        return {**result}

    def attachments(self):
        for setting in self.settings:
            yield from setting.attachments()

    def rich_fields(self):
        for setting in self.settings:
            yield from setting.rich_fields()

    def map_rich_fields(self, callback):
        new_settings = []
        for setting in self.settings:
            setting.transform_rich_field(callback)
            new_settings.append(setting.serialize())
        self.widget['settings'] = new_settings


class WidgetSettingSerializer(WidgetSerializerBase):
    def __init__(self, setting, acting_user=None):
        self.setting = setting
        self.acting_user = acting_user

    @property
    def key(self):
        return self.setting.get('key')

    @property
    def value(self):
        return self.setting.get('value')

    @property
    def richDescription(self):
        if self.setting.get('richDescription'):
            return self.setting.get('richDescription')
        if self.setting.get('key') == 'richDescription' and self.setting.get('value'):
            return self.setting.get('value')

    @property
    def attachmentId(self):
        from core.models import Attachment
        if not self.setting.get('attachmentId') and self.setting.get('attachment') and self.acting_user:
            attachment_input = self.setting.get('attachment')
            try:
                attachment = Attachment.objects.get(id=attachment_input.get('id'))
            except (Attachment.DoesNotExist, ValidationError, AttributeError):
                attachment = Attachment.objects.create(upload=attachment_input, owner=self.acting_user)
            self.setting['attachmentId'] = str(attachment.id)
        return self.setting.get('attachmentId')

    @property
    def attachment(self):
        from core.models import Attachment
        if self.attachmentId:
            return Attachment.objects.filter(id=self.attachmentId).first()

    def serialize(self):
        return {
            'key': self.key,
            'value': self.value,
            'richDescription': self.richDescription,
            'attachmentId': self.attachmentId,
        }

    def attachments(self):
        if self.attachmentId:
            yield self.attachmentId

    def rich_fields(self):
        if self.richDescription:
            yield self.richDescription

    def transform_rich_field(self, callback):
        if self.setting.get('key') == 'richDescription' and self.setting.get('value'):
            self.setting['value'] = callback(self.setting['value'])
        elif self.setting.get('richDescription'):
            self.setting['richDescription'] = callback(self.setting['richDescription'])
