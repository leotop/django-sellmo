from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import StaticNode
from django.conf import settings

register = template.Library()


def static(path):
    gulp_url = getattr(settings, 'GULP_URL', None)
    if getattr(settings, 'DEBUG', False) and gulp_url:
        return '%s%s' % (gulp_url, path)
    return staticfiles_storage.url(path)


class StaticFilesNode(StaticNode):

    def url(self, context):
        path = self.path.resolve(context)
        return static(path)


@register.tag('gulp_or_static')
def do_static(parser, token):
    return StaticFilesNode.handle_token(parser, token)