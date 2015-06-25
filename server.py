import os
import sys
import math
import hashlib

from django.conf import settings

DEBUG = os.environ.get('DEBUG', 'on') == 'on'

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

BASE_DIR = os.path.dirname(__file__)

settings.configure(
  DEBUG=DEBUG,
  SECRET_KEY=SECRET_KEY,
  ALLOWED_HOSTS=ALLOWED_HOSTS,
  ROOT_URLCONF=__name__,
  MIDDLEWARE_CLASSES=(
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
  ),
  INSTALLED_APPS=(
    'django.contrib.staticfiles',
  ),
  TEMPLATE_DIRS=(
    os.path.join(BASE_DIR, 'templates'),
  ),
  STATICFILES_DIRS=(
    os.path.join(BASE_DIR, 'static'),
  ),
  STATIC_URL='/static/',
)

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django import forms
from django.conf.urls import url
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import etag

class TileForm(forms.Form):

    lod = forms.IntegerField(min_value=0, max_value=100)
    y = forms.IntegerField(min_value=0, max_value=10000000)
    x = forms.IntegerField(min_value=0, max_value=10000000)

    def generate(self, image_format='PNG'):
        lod = self.cleaned_data['lod']
        y = self.cleaned_data['y']
        x = self.cleaned_data['x']

        key = '{}.{}.{}'.format(lod, y, x)
        content = cache.get(key)
        if content:
            return content

        height = 256
        width = 256

        text_size_divisor = 9

        image = Image.new('RGB', (width, height), "gray")
        draw = ImageDraw.Draw(image)
        text = '{}/{}/{}'.format(lod, y, x)

        image_size = math.sqrt(image.size[0] * image.size[1])
        fontsize = math.floor(image_size / text_size_divisor)
        font = ImageFont.truetype("fonts/SourceSansPro-Regular.ttf", fontsize)
        textwidth, textheight = font.getsize(text)

        if textwidth > width:
            fontsize = math.floor(image.size[0] / text_size_divisor)
            font = ImageFont.truetype("fonts/SourceSansPro-Regular.ttf", fontsize)
            textwidth, textheight = font.getsize(text)
        elif textheight > height:
            fontsize = math.floor(image.size[1] / text_size_divisor)
            font = ImageFont.truetype("fonts/SourceSansPro-Regular.ttf", fontsize)
            textwidth, textheight = font.getsize(text)

        texttop = (height / 2) - (textheight / 1.45)# - (height * 0.04)
        textleft = (width / 2) - (textwidth / 2)

        draw.text((textleft, texttop), text, font=font, fill=(150, 255, 255))

        content = BytesIO()
        image.save(content, image_format)
        content.seek(0)

        cache.set(key, content, 60 * 60)

        return content

def generate_tile_etag(request, lod, y, x):
    content = 'Tile: {} / {} / {}'.format(lod, y, x)
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

@etag(generate_tile_etag)
def tile(request, lod, y, x):
  form = TileForm({'lod': lod,'y': y, 'x': x})
  if form.is_valid():
    image = form.generate()
    return HttpResponse(image, content_type='image/png')
  else:
    return HttpResponseBadRequest('Invalid Tile Request')

def index(request):
  example = reverse('tile', kwargs={'lod':1, 'y':2375, 'x':1873})
  context = {
    'example': request.build_absolute_uri(example)
  }
  return render(request, 'home.html', context)

def service_description(request):
    query_string = request.GET.get('f')
    #if query_string == "jsapi":
    #    return render(request, 'viewer.html')
    if query_string == "json":
        return render(request, 'service_description.json')
    else:
        return render(request, 'service_description.html')

def viewer(request):
    return render(request, 'viewer.html')

urlpatterns = (
  url(r'^GIS/REST/MapTiled/GreyScale/MapServer/tile/(?P<lod>[0-9]+)/(?P<y>[0-9]+)/(?P<x>[0-9]+)', tile, name='tile'),
  url(r'^GIS/REST/MapTiled/GreyScale/MapServer', service_description, name='service_description'),
  url(r'^GIS/REST/MapTiled/GreyScale/Viewer', viewer, name='viewer'),
  url(r'^$', index, name='homepage'),
)

application = get_wsgi_application()

if __name__ == "__main__":
  from django.core.management import execute_from_command_line

  execute_from_command_line(sys.argv)
