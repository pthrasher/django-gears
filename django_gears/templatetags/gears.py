from __future__ import absolute_import
from django.template import Node, Library, TemplateSyntaxError
from gears.assets import build_asset
from ..settings import environment, GEARS_URL, GEARS_DEBUG, GEARS_CACHE_BUST


register = Library()


class AssetTagNode(Node):

    def __init__(self, logical_path, debug, cache_bust):
        self.logical_path = logical_path
        self.debug = debug
        self.cache_bust = cache_bust

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) not in (2, 3, 4):
            msg = '%r tag takes one argument: the logical path to the public asset'
            raise TemplateSyntaxError(msg % bits[0])
        debug = (len(bits) == 3 or len(bits) == 4)
        if debug and bits[2] != 'debug':
            msg = "Second (optional) argument to %r tag must be 'debug'"
            raise TemplateSyntaxError(msg % bits[0])
        cache_bust = (len(bits) == 4)
        if cache_bust and bits[3] != 'cache_bust':
            msg = "Third (optional) argument to %r tag must be 'cache_bust'"
            raise TemplateSyntaxError(msg % bits[0])
        logical_path = parser.compile_filter(bits[1])
        return cls(logical_path, debug, cache_bust)


    def render(self, context):
        logical_path = self.logical_path.resolve(context)
        if self.debug or GEARS_DEBUG:
            asset = build_asset(environment, logical_path)
            if self.cache_bust or GEARS_CACHE_BUST:
                paths = (('%s?body=1&v=%s' % (r.attributes.logical_path, r.mtime))\
                    for r in asset.requirements)
            else:
                paths = (('%s?body=1' % (r.attributes.logical_path,))\
                    for r in asset.requirements)
        else:
            if logical_path in environment.manifest.files:
                logical_path = environment.manifest.files[logical_path]
            paths = (logical_path,)
        return '\n'.join((self.template % path) for path in paths)


class CSSAssetTagNode(AssetTagNode):

    template = u'<link rel="stylesheet" href="%s%%s">' % GEARS_URL


class JSAssetTagNode(AssetTagNode):

    template = u'<script src="%s%%s"></script>' % GEARS_URL


@register.tag
def css_asset_tag(parser, token):
    return CSSAssetTagNode.handle_token(parser, token)


@register.tag
def js_asset_tag(parser, token):
    return JSAssetTagNode.handle_token(parser, token)
