from models import Article, Category
import os
from os import path
import yaml
import settings
from docutils.core import publish_parts
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe

_precontent = '''\
**********
Fake Title
**********
+++++++++++++
Fake Subtitle
+++++++++++++

'''


def _preprocess(value):
    # This is adapted from django source
    value = _precontent + value
    docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
    parts = publish_parts(source=smart_str(value), writer_name="html4css1", settings_overrides=docutils_settings)
    return mark_safe(force_unicode(parts["fragment"]))


def loaddir(directory, clear=False):
    if clear:
        Category.objects.all().delete()
        Article.objects.all().delete()
    categories = {}
    for cat in yaml.load(file(directory + '/categories')):
        C = Category(name=cat['name'], slug=cat['slug'])
        C.save()
        categories[cat['slug']] = C

    queue = os.listdir(directory)
    while queue:
        artfile = queue.pop()
        if artfile[0] == '.': continue
        if artfile in ('categories', 'template'): continue
        artfile = path.join(directory, artfile)
        if path.isdir(artfile):
            queue.extend([
                path.join(artfile,f) for f in os.listdir(artfile)
                ])
            continue

        input = file(artfile)
        header = {}
        linenr = 0
        while True:
            line = input.readline().strip()
            linenr += 1
            if line == '..': break
            tag,value = line.split(':')
            value = value.strip()
            header[tag] = value
        blank = input.readline()
        linenr += 1
        if blank.strip():
            raise IOError, 'Blank line expected while processing file (%s:%s)\nGot "%s"' % (artfile, linenr,blank)
        content = input.read()
        content = _preprocess(content)
        A = Article(title=header['title'], url=header['url'], content=content)
        A.save()
        for c in header.get('categories','').split():
            A.categories.add(categories[c])

