from django import template
from django.template import resolve_variable
from django.conf import settings
from django.db.models import Q
from django.template.defaultfilters import filesizeformat, date as date_filter
from django.utils.html import strip_spaces_between_tags
from django.utils.text import smart_split
from django.utils.translation import ugettext_lazy as _

from sorl.thumbnail.main import DjangoThumbnail

try:
    from photologue.models import Photo, PhotoSize, PhotoSizeCache
    has_photologue = True
except ImportError:
    has_photologue = False

from video.models import Video

import os
import re
import types
from stat import *
from PIL import Image

register = template.Library()

FILE_TYPES = {
    'pdf': 'PDF',
    'xls': 'Excel',
    'flv': 'Flash',
}

FILE_TAG = '<a class="%(ext)s" href="%(url)s">%(title)s (%(type)s, %(size)s)</a>'

IMG_TAG = '<img class="photo" src="%(url)s" alt="%(title)s" width="%(width)s" height="%(height)s" />'

CAPTIONED_IMG_TAG = '<div class="photo image-with-caption"><img src="%(url)s" alt="%(title)s" width="%(width)s" height="%(height)s" /><p>%(title)s</p></div>'

PDF_TAG = '<a class="file-link pdf" href="%(url)s">%(title)s</a> <span class="file-info">Updated %(date)s (PDF, %(size)s)</span>'

SIZE_RE = re.compile(r'(?P<width>\d+)x(?P<height>\d+)')
TAG_RE = re.compile(r'\[\[(?P<text>.*?)\]\]')

PHOTO_TAG = """
<div class="photo">
  <a href="%(full_url)s" title="%(title)s" rel="%(rel)s" class="lightbox">
    <img src="%(thumbnail_url)s" alt="%(title)s" zoom="%(display_url)s" orig="%(full_specs)s" />
  </a>
  %(caption)s
</div>
"""

def _strip(str):
    if str[0] in ("'", '"') and str[0] == str[-1]:
        return str[1:-1]
    return str

def _render_photo(photo, params):
    sizes = PhotoSizeCache().sizes
    size = 'thumbnail'
    rel = None
    for param in params:
        if param in sizes.keys():
            size = param
            params.remove(param)
    if params:
        rel = params[0]

    thumbnail_url = getattr(photo, 'get_%s_url' % size)()

    if photo.caption:
        caption = '<span class="caption">%s</span>' % photo.caption
    else:
        caption = ''

    display_size = sizes['display']
    im = Image.open(photo.image.path)
    if im.size[0] > display_size.size[0] or im.size[1] > display_size.size[1]:
        full_url = photo.image.url
        full_specs = '%sx%s' % im.size
        display_url = photo.get_display_url()
    else:
        full_url = photo.get_display_url()
        display_url = full_specs = ''

    kw = {
        'display_url': display_url,
        'full_url': full_url,
        'thumbnail_url': thumbnail_url,
        'title': photo.title,
        'full_specs': full_specs,
        'rel': rel,
        'class': '',
        'caption': caption,
    }
    tag = PHOTO_TAG % kw
    return strip_spaces_between_tags(tag)

def _render_pdf(pdf, params):
    kw = {
        'url': pdf.file.url,
        'title': pdf.title,
        'size': pdf.size,
        'date': date_filter(pdf.date, 'N jS, Y'),
    }
    return PDF_TAG % kw

def _render_video(video, params):
    t = template.loader.get_template('video/video_snippet.html')
    metadata = video.metadata()

    player_width = metadata['width'];
    ctx = template.Context({
        'video': video,
        'metadata': metadata,
        'media_url': settings.MEDIA_URL,
    })
    return t.render(ctx)

class PhotoNode(template.Node):

    def __init__(self, photo, params):
        self.photo, self.params = photo, [_strip(p) for p in params]

    def render(self, context):
        photo = context.get(self.photo)
        return _render_photo(photo, self.params)

@register.tag
def photo(parser, token):
    params = token.split_contents()
    name = params[0]
    try:
        photo = params[1]
    except IndexError:
        raise template.TemplateSyntaxError, '%s tag requires at least one argument' % name

    return PhotoNode(photo, params[2:])

@register.simple_tag
def file_link(file, title=None):
    if isinstance(file, types.StringTypes):
        name = file
    else:
        name = file._name
    path = os.path.join(settings.MEDIA_ROOT, name)
    ext = name[name.rfind('.')+1:].lower()
    title = title or name[name.rfind('/')+1:]
    size = os.stat(path)[ST_SIZE]

    return FILE_TAG % {
        'url': settings.MEDIA_URL + name,
        'title': title,
        'size': filesizeformat(size),
        'ext': ext,
        'type': FILE_TYPES[ext],
    }

class ShowImageNode(template.Node):

    def __init__(self, file, title, width, height):
        self.file, self.title, self.width, self.height = file, title, width, height

    def render(self, context):
        im = Image.open(os.path.join(settings.MEDIA_ROOT, self.file))
        width, height = im.size
    
        #if width <= self.width and height <= self.height:
                
        tag = IMG_TAG
        tag = self.title is not None and CAPTIONED_IMG_TAG or IMG_TAG

        thumbnail = unicode(DjangoThumbnail(self.file, (100, 100)))

        return tag % {
            'url': thumbnail,
            'title': self.title,
            'width': width,
            'height': height,
        }

@register.tag
def show_image(parser, token):
    params = token.split_contents()
    name = params[0]

    try:
        file = _strip(params[1])
    except IndexError:
        raise template.TemplateSyntaxError, '%s tag requires at least one argument' % params[0]

    title = width = height = None
    for param in params[2:]:
        if param[-1] == 'w':
            width = int(param[:-1])
        elif param[-1] == 'h':
            height = int(param[:-1])
        else:
            title = _strip(param)

    return ShowImageNode(file, title, width, height)

def _render_media_tag(file, opts):
    ext = file[file.rfind('.')+1:].lower()

    if ext in ('flv', 'mp4'):
        from video.models import Video
        try:
            video = Video.objects.get(flv_file=file)
        except Video.DoesNotExist:
            return u''
        t = template.loader.get_template('video/video_snippet.html')
        ctx = template.Context({
            'video': video,
            'metadata': video.metadata(),
            'media_url': settings.MEDIA_URL,
        })
        return t.render(ctx)

    elif ext in ('gif', 'jpg', 'jpeg', 'png'):
        try:
            im = Image.open(os.path.join(settings.MEDIA_ROOT, file))
        except IOError:
            return u''
        width = opts.get('width', im.size[0])
        height = opts.get('height', im.size[1])
        thumbnail = unicode(DjangoThumbnail(file, (width, height)))
        img_tag = IMG_TAG % {
            'url': thumbnail,
            'title': 'test',
            'width': width,
            'height': height,
        }
        return '<a class="lightbox" href="%(url)s">%(img)s</a>' % { 'url': settings.MEDIA_URL + file, 'img': img_tag }

    else:
        title = opts.get('title', file[file.rfind('/')+1:])
        try:
            size = os.stat(os.path.join(settings.MEDIA_ROOT, file))[ST_SIZE]
        except OSError:
            return u''

        return FILE_TAG % {
            'url': file,
            'title': title,
            'size': filesizeformat(size),
            'ext': ext,
            'type': FILE_TYPES[ext],
        }

def _get_photo(query):
    q = Q(title=query) | Q(title_slug=query)
    try:
        int(query)
    except ValueError:
        pass
    else:
        q = q | Q(id=query)

    results = Photo.objects.filter(q)
    try:
        return results[0]
    except IndexError:
        return None

def _get_video(query):
    q = Q(title=query) | Q(upload_file=query) | Q(flv_file=query)
    try:
        int(query)
    except ValueError:
        pass
    else:
        q = q | Q(id=query)

    results = Video.objects.filter(q)
    try:
        return results[0]
    except IndexError:
        return None

from mmyc.content.models import PDF
def _get_pdf(query):
    q = Q(title=query)
    try:
        int(query)
    except ValueError:
        pass
    else:
        q = q | Q(id=query)

    results = PDF.objects.filter(q)
    try:
        return results[0]
    except IndexError:
        return None

@register.filter
def convert_media_tags(value):

    def _media_tags_process(groups):
        params = list(smart_split(groups.group('text')))

        if params[0] == 'photo':
            if not has_photologue:
                if settings.DEBUG:
                    raise Exception, '[[photo]] tag found but photologue app not installed.'
                else:
                    return u''
            photo = _get_photo(_strip(params[1]))
            return photo and _render_photo(photo, params[2:]) or u''

        if params[0] == 'video':
            video = _get_video(_strip(params[1]))
            return video and _render_video(video, params[2:]) or u''

        if params[0] == 'pdf':
            pdf = _get_pdf(_strip(params[1]))
            return pdf and _render_pdf(pdf, params[2:]) or u''

        file = _strip(params[0])
        opts = {}
        for param in params[1:]:
            param = _strip(param)
            m = SIZE_RE.match(param)
            if m:
                opts['width'] = m.group('width')
                opts['height'] = m.group('height')
            elif opts.has_key('title'):
                opts['caption'] = param
            else:
                opts['title'] = param
        return _render_media_tag(file, opts)

    return TAG_RE.sub(_media_tags_process, value.replace('&quot;', '"'))
convert_media_tags.is_safe = True



# [[video/flv/movie.flv]]
# [["content/photo.jpg" "Photo 1" 100x100]]
# [["content/photo.jpg" "Photo 1" "My boat, see it and tremble"]]
# [["pdfs/Download.pdf" "Download this and read it"]]
# [[photo 10]]
# [[photo 12 larger]]
