from collections import defaultdict

from core.widget_resolver import WidgetSerializerBase, WidgetSerializer


class RowSerializer(WidgetSerializerBase):
    def __init__(self, row: dict, acting_user=None):
        self.row = row
        self.acting_user = acting_user

    @property
    def isFullWidth(self):
        return self.row.get('isFullWidth')

    @property
    def columns(self):
        return [ColumnSerializer(c, self.acting_user) for c in self.row.get('columns', []) or []]

    def serialize(self):
        result = defaultdict(list)
        result['isFullWidth'] = self.isFullWidth
        for column in self.columns:
            result['columns'].append(column.serialize())
        return result

    def attachments(self):
        for column in self.columns:
            yield from column.attachments()

    def rich_fields(self):
        for column in self.columns:
            yield from column.rich_fields()


class ColumnSerializer(WidgetSerializerBase):
    def __init__(self, column, acting_user=None):
        self.column = column
        self.acting_user = acting_user

    @property
    def width(self):
        return self.column.get('width')

    @property
    def widgets(self):
        return [WidgetSerializer(w, self.acting_user) for w in self.column.get('widgets', []) or []]

    def serialize(self):
        result = defaultdict(list)
        result['width'] = self.width
        for widget in self.widgets:
            result['widgets'].append(widget.serialize())
        return result

    def attachments(self):
        for widget in self.widgets:
            yield from widget.attachments()

    def rich_fields(self):
        for widget in self.widgets:
            yield from widget.rich_fields()