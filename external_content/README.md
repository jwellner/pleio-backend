Module demo
===

```python
from external_content.models import ExternalContentSource
from external_content.api_handlers.default import ApiHandler as DefaultHandler

ExternalContentSource.objects.get_or_create(
    name="Demo",
    handler_id=DefaultHandler.ID,
)
```