import logging
import re
from random import choice
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from src.utils import pr, choose, ask, fc, fx, fy, REQ_S

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, sb, init_path: str):
        self.sb = sb
        self.emails = set()
        self.external_res = set()
        self.crawled_paths = set()
        self.known_paths = set('/')
        if init_path:
            self.known_paths.add(init_path)

    def show_menu(self):
        while 1:
            c = choose(['Emails', 'External Resources',
                        'Known Paths', 'Crawled Paths'])
            if c < 0:
                break
            li = (self.emails, self.external_res,
                  self.known_paths, self.crawled_paths)[c]
            if not li:
                pr('Nothing to show yet!', '!')
            for i in li:
                pr(i, '#')

    def menu(self):
        while 1:
            pr(f'Emails: {fc}{len(self.emails)}')
            pr(f'External resources: {fc}{len(self.external_res)}')
            pr(f'Internal known paths: {fc}{len(self.known_paths)}')
            pr(f'Crawled paths: {fc}{len(self.crawled_paths)}')
            c = choose(['Show', 'Google Crawl', 'BS Crawl'],
                       'Choose crawling engine')
            if c < 0:
                break
            if c == 0:
                self.show_menu()
            elif c == 1:
                try:
                    self.google()
                except KeyboardInterrupt:
                    pr('Stopped!', '!')
            elif c == 2:
                try:
                    while 1:
                        avail = list(self.known_paths - self.crawled_paths)
                        if not avail:
                            pr('No crawlable pages!', '!')
                            break
                        page = choice(avail)
                        self.crawl(page)
                        self.crawled_paths.add(page)

                except KeyboardInterrupt:
                    pr('Crawling stopped', '!')

    def google(self):
        for loop in range(0, int(ask('How many pages?'))):
            url = f"https://google.com/search?q=site:{self.sb.domain}&ie=utf-8&oe=utf-8&aq=t&start={str(loop)}0"
            res = REQ_S.get(url)
            if res.status_code != 200:
                pr('Bad status code: %d' % res.status_code, '!')
                return
            c = 0
            soup = BeautifulSoup(res.content, 'html.parser')
            for l in soup.find_all('cite'):
                if not l.span:
                    continue
                # print(l)
                ls = urlsplit('http://' + l.span.decode_contents())
                if self.sb.domain not in ls.netloc:
                    pr('Wrong domain found: ' + fy + ls.path + fx, '!')
                    continue

                pts = ls.netloc.split('.')
                if len(pts) > 2 and ls.netloc not in self.sb.known_subdomains:
                    pr('Found new subdomain: ' + fc + ls.netloc + fx)
                    continue

                if ls.path not in self.known_paths:
                    self.known_paths.add(ls.path)
                    c += 1
            pr(f'Added {c} new paths')

    def crawl(self, page):
        pr('Crawling page: ' + fc + page + fx)

        url = self.sb.pack_url(path=page)
        res = REQ_S.get(url)
        if res.status_code == 404:
            i = f'page: "{page}" is 404'
            logger.info(i)
            pr(i, '!')
            return
        elif res.status_code != 200:
            i = f'page returned code "{res.status_code}" <=> "{page}" '
            logger.info(i)
            pr(i, '!')
            return

        il = xl = 0
        soup = BeautifulSoup(res.content, 'html.parser')
        # Links are in ['a', 'link', 'img', 'svg', 'iframe', 'embed', 'audio']
        for k, v in {'a': 'href',
                     'link': 'href',
                     'iframe': 'src',
                     'embed': 'src'}.items():
            for l in soup.find_all(k):
                try:
                    x = l[v].lower()
                except KeyError:
                    i = f'"{page}" KeyError: No link found in "{k}" element'
                    logger.info(i)
                    pr(i, '!')
                    continue
                if x.startswith('#'):
                    continue
                if x.endswith('.ico'):
                    continue

                if x.startswith('/'):
                    x = url + x

                if re.match(r'[^@]+@[^@]+\.[^@]+', x):  # Email
                    if x not in self.emails:
                        pr('Found new email: ' + fc + x + fx)
                        self.emails.add(x)
                    continue

                ux = urlsplit(x)
                if self.sb.domain not in ux.netloc:
                    self.external_res.add(x)
                    xl += 1
                    continue
                final = ux.path.replace('//', '/')  # replacing as a workaround

                if final not in self.known_paths:
                    self.known_paths.add(final)
                    il += 1

        # pr(f'Found {fc}{il}{fx} new Internal paths')
        # pr(f'Found {fc}{xl}{fx} new External resources')
