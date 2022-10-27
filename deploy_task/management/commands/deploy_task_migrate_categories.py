from core.post_deploy import migrate_categories, strip_article_images_of_exif_data, migrate_widgets_for_match_strategy

from deploy_task.utils import DeployCommandBase


class Command(DeployCommandBase):
    deploy_task = 'deploy_task.management.commands.deploy_categories.deploy_task'


def deploy_task():
    migrate_categories()
    migrate_widgets_for_match_strategy()
    strip_article_images_of_exif_data()
