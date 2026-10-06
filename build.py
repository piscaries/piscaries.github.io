#!/usr/bin/env python3
"""Build the static site: src/ (Markdown posts, images, about) -> docs/ (served by GitHub Pages).

usage: python3 build.py          # needs pandoc on PATH
"""
import html, os, re, shutil, subprocess
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(ROOT, 'src'), os.path.join(ROOT, 'docs')
SITE = {
    'title': 'Haifeng (Kevin) Zhao',
    'tagline': 'Notes on building with LLMs and coding agents',
    'url': 'https://piscaries.github.io',
}


def read_post(path):
    text = open(path, encoding='utf-8').read()
    _, fm, body = text.split('---\n', 2)
    meta = {}
    for line in fm.strip().splitlines():
        k, v = line.split(':', 1)
        meta[k.strip()] = v.strip().strip('"')
    name = os.path.basename(path)[:-3]
    meta['date'] = name[:10]
    meta['slug'] = name[11:]
    meta['body'] = body
    return meta


def md_to_html(md):
    return subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html5', '--no-highlight'],
                          input=md, capture_output=True, text=True, check=True).stdout


def page(title, description, path, content, og_type='website', image=None):
    e = html.escape
    url = SITE['url'] + path
    img = f'<meta property="og:image" content="{SITE["url"]}{image}">' if image else ''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{url}">
{img}
<meta name="twitter:card" content="{'summary_large_image' if image else 'summary'}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="{e(SITE['title'])}" href="/feed.xml">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site"><a class="name" href="/">{e(SITE['title'])}</a><nav><a href="/">Writing</a><a href="/about/">About</a><a href="/feed.xml">RSS</a></nav></header>
<main>
{content}
</main>
<footer class="site">© {datetime.now().year} {e(SITE['title'])} · <a href="https://github.com/piscaries">GitHub</a></footer>
</body>
</html>
'''


def nice_date(d):
    return datetime.strptime(d, '%Y-%m-%d').strftime('%B %-d, %Y')


def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(SRC, 'images'), os.path.join(OUT, 'images'))
    shutil.copy(os.path.join(ROOT, 'style.css'), os.path.join(OUT, 'style.css'))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    posts = [read_post(os.path.join(SRC, 'posts', f)) for f in os.listdir(os.path.join(SRC, 'posts')) if f.endswith('.md')]
    posts.sort(key=lambda p: p['date'], reverse=True)
    e = html.escape

    for p in posts:
        body = md_to_html(p['body'])
        notes = []
        if p.get('original'):
            notes.append(f'Originally published on <a href="{e(p["original"])}">Medium</a>.')
        if p.get('repo'):
            notes.append(f'Code, data and reproduction steps: <a href="{e(p["repo"])}">{e(p["repo"].replace("https://", ""))}</a>.')
        note = f'<p class="note">{" ".join(notes)}</p>' if notes else ''
        first_img = re.search(r'<img\s[^>]*?src="([^"]+)"', body, re.S)
        preview = p.get('image') or (first_img.group(1) if first_img else None)
        content = f'''<article>
<h1>{e(p["title"])}</h1>
<p class="meta"><time datetime="{p["date"]}">{nice_date(p["date"])}</time></p>
{note}
{body}
</article>
<p class="back"><a href="/">← All writing</a></p>'''
        d = os.path.join(OUT, 'posts', p['slug'])
        os.makedirs(d)
        open(os.path.join(d, 'index.html'), 'w').write(
            page(f'{p["title"]} · {SITE["title"]}', p.get('description', ''), f'/posts/{p["slug"]}/', content,
                 'article', preview))

    items = '\n'.join(
        f'<li><a href="/posts/{p["slug"]}/">{e(p["title"])}</a>'
        f'<span class="meta"><time datetime="{p["date"]}">{nice_date(p["date"])}</time></span>'
        f'<p>{e(p.get("description", ""))}</p></li>' for p in posts)
    index = f'<p class="tagline">{e(SITE["tagline"])}</p>\n<ul class="posts">\n{items}\n</ul>'
    open(os.path.join(OUT, 'index.html'), 'w').write(page(SITE['title'], SITE['tagline'], '/', index))

    about_md = open(os.path.join(SRC, 'about.md')).read()
    os.makedirs(os.path.join(OUT, 'about'))
    open(os.path.join(OUT, 'about', 'index.html'), 'w').write(
        page(f'About · {SITE["title"]}', SITE['tagline'], '/about/', f'<article>{md_to_html(about_md)}</article>'))

    open(os.path.join(OUT, '404.html'), 'w').write(
        page('Not found', '', '/404.html', '<h1>Not found</h1><p><a href="/">Back to all writing</a></p>'))

    rss_items = '\n'.join(
        f'<item><title>{e(p["title"])}</title><link>{SITE["url"]}/posts/{p["slug"]}/</link>'
        f'<guid>{SITE["url"]}/posts/{p["slug"]}/</guid>'
        f'<pubDate>{datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc).strftime("%a, %d %b %Y 00:00:00 +0000")}</pubDate>'
        f'<description>{e(p.get("description", ""))}</description></item>' for p in posts)
    open(os.path.join(OUT, 'feed.xml'), 'w').write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{e(SITE["title"])}</title>'
        f'<link>{SITE["url"]}</link><description>{e(SITE["tagline"])}</description>\n{rss_items}\n</channel></rss>\n')
    print(f'built {len(posts)} posts into docs/')


if __name__ == '__main__':
    build()
