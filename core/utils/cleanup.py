from core.models import Entity


def schedule_cleanup_group_content_featured_images(group):
    # pylint: disable=import-outside-toplevel
    from core.tasks.cleanup_tasks import cleanup_featured_image_files
    for entity in Entity.objects.filter(group=group).select_subclasses():
        if hasattr(entity, 'featured_image'):
            cleanup_featured_image_files(entity.featured_image.guid if entity.featured_image else None)
    cleanup_featured_image_files(group.featured_image.guid if group.featured_image else None)
