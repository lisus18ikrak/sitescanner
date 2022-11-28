import os
import re
import socket
import sys
from urllib.parse import urlsplit, urlunsplit

import bs4
import requests

from src.crawler import Crawler
from src.utils import REQ_S, pr, pause, ask, fc, fx, fr, fg


class Domainator:

    def __init__(self):
        # Parse arguemnts
        if len(sys.argv) > 1:
            arg = sys.argv[1]
        else:
            arg = ask('Enter domain:')
            if not arg:
                exit()

        # Verify domain integrity
        if '://' in arg:
            parsed = urlsplit(arg)
        else:
            parsed = urlsplit('http://' + arg)
        if '.' not in parsed.netloc:
            pr('Invalid domain!', '!')
            exit()

        # Verify subdomain
        self.subdomain = self.base_domain = None
        pts = parsed.netloc.split('.')
        if len(pts) > 2:
            pr('Is this the subdomain you wish to use:? ' + pts[0])
            if pause('agree', cancel=True):  # subdomain
                self.subdomain = pts[0]
                self.base_domain = '.'.join(pts[1:])
        if not self.subdomain:
            self.subdomain = 'www'
        if not self.base_domain:
            self.base_domain = parsed.netloc

        self.domain = parsed.netloc
        self.scheme = parsed.scheme if parsed.scheme else 'http'
        print()
        pr('Using domain: ' + fc + self.domain + fx)

        self.crawler = Crawler(self, parsed.path)

        # self.ip = IPv4Address(socket.gethostbyname(self.domain))
        # pr('Host resolved: ' + cl.c + str(self.ip))

    def pack_url(self, subdomain=None, path=''):
        if not subdomain:
            subdomain = self.subdomain
        return urlunsplit((self.scheme, subdomain + '.' + self.base_domain, path, '', ''))

    def banners_cloud_flare(self):
        pr('Retrieving headers', '#')
        domain = self.pack_url()
        res = REQ_S.get(domain)
        if res.status_code != 200:
            pr('Bad status code: %d' % res.status_code, '!')
            return

        pr('Headers:')
        for h in res.headers.items():
            x = f'{h[0]} => {h[1]}'
            pr(x, '#')

        pr('Checking for CloudFlare in headers', '#')
        if "cloudflare" not in res.text:
            pr(self.domain + " is not using Cloudflare!")
            return

        if not pause('Attempt to bypass?', cancel=True):
            return
        pr("CloudFlare found, attempting to bypass..")

        # TODO TEST

        url = "http://www.crimeflare.biz/cgi-bin/cfsearch.cgi"
        res = REQ_S.get(url, data={'cfS': self.domain})
        reg = re.findall(r'\d+\.\d+\.\d+\.\d+', res.text)
        if reg:
            real_ip = reg[1]
        else:
            pr("CloudFlare wasn't bypassed, No real IP found", '!')
            return
        res = REQ_S.get(f"http://{real_ip}")
        if "cloudflare" not in res.text.lower():
            if real_ip:
                pr("Cloudflare Bypassed!", '#')
                pr('===============================')
                pr("Real IP ==> " + fc + real_ip + fx)
                pr('===============================')
            return
        pr("Cloudflare wasn't bypassed, Real IP blocked by CloudFlare", '!')

    def reverse_HT(self):
        url = "http://api.hackertarget.com/reverseiplookup/?q=" + self.domain
        res = REQ_S.get(url)
        if res.status_code != 200:
            pr('Bad status code: %d' % res.status_code, '!')
            return
        lst = res.text.strip().split("\n")

        reverse_dir = './reverseip'
        if not os.path.isdir(reverse_dir):
            os.mkdir(reverse_dir)

        fn = os.path.join(reverse_dir, f'ht-{self.domain}')
        with open(fn, 'w') as f:
            for l in lst:
                if l:
                    f.write(l.strip() + '\n')
                    # pr(l, '#')
        print()
        pr(f'Dumped {len(lst)} entries to "{fn}"\n')

    def reverse_YGS(self):  # TODO record to file
        url = "https://domains.yougetsignal.com/domains.php"
        data = {
            'remoteAddress': self.domain,
            'key': ''
        }
        res = REQ_S.get(url, params=data)
        if res.status_code != 200:
            pr('Bad status code: %d' % res.status_code, '!')
            # return

        grab = res.json()
        if 'fail' in grab['status'].lower():
            pr("Message:", '#')
            print(grab['message'])
            return

        pr("Results from: " + grab['lastScrape'], '#')
        pr("IP: " + grab['remoteIpAddress'], '#')
        pr("Domain: " + grab['remoteAddress'], '#')
        pr(f"Total Domains: {grab['domainCount']}\n", '#')
        for x, _ in grab['domainArray']:
            pr(x, '#')

    def find_subdomains(self):
        print("{}{:<62}| {:<50}{}".format(fc, "URL", "STATUS", fx))
        with open('./src/subdomains') as f:
            for sub in f:
                if sub == self.subdomain:
                    continue

                sub = sub.strip()
                url = self.pack_url(subdomain=sub)
                try:
                    res = REQ_S.get(url)
                    if res.status_code != 404:
                        print("{}{:<62}| {:<50}{}".format(
                            fg, url, res.status_code, fx))
                except KeyboardInterrupt:
                    pr('Scan stopped!', '!')
                    break
                except:
                    print("{}{:<62}| {:<50}{}".format(fr, url, 'ERROR', fx))

    def speed_check(self):
        import time

        start = time.time()
        ip = socket.gethostbyname(self.domain)
        dns_tm = time.time() - start
        _dns = "{:<10}:{:<20} seconds".format("DNS", dns_tm)
        pr(_dns, '#')

        start = time.time()
        _data = REQ_S.get(self.pack_url())
        load_tm = time.time() - start
        _load = "{:<10}:{:<20} seconds".format("Load", load_tm)
        _wo = "{:<10}:{:<20} seconds".format("W/O DNS", load_tm - dns_tm)

        pr(_load, '#')
        pr(_wo, '#')

    def whois(self):
        url = 'https://www.whois.com/whois/' + self.domain
        try:
            res = REQ_S.get(url)
            if res.status_code != 200:
                pr('Bad status code: %d' % res.status_code, '!')
                return
            bs = bs4.BeautifulSoup(res.content, 'html.parser')
            result = bs.find_all(
                'pre', {'class': 'df-raw'})[0].decode_contents()
            print(f"\n{fc + result + fx}")
        except requests.exceptions.RequestException:
            from traceback import print_exc
            print_exc()

    def find_panels(self):
        pr("Searching for admin panels", '#')
        pth_lst = (
            'admin/', 'site/admin', 'admin.php/', 'up/admin/', 'central/admin/', 'whm/admin/', 'whmcs/admin/',
            'support/admin/', 'upload/admin/', 'video/admin/', 'shop/admin/', 'shoping/admin/', 'wp-admin/',
            'wp/wp-admin/', 'blog/wp-admin/', 'admincp/', 'admincp.php/', 'vb/admincp/', 'forum/admincp/',
            'up/admincp/', 'administrator/', 'administrator.php/', 'joomla/administrator/', 'jm/administrator/',
            'site/administrator/', 'install/', 'vb/install/', 'dimcp/', 'clientes/', 'admin_cp/', 'login/', 'login.php',
            'site/login', 'site/login.php', 'up/login/', 'up/login.php', 'cp.php', 'up/cp', 'cp', 'master', 'adm',
            'member', 'control', 'webmaster', 'myadmin', 'admin_cp', 'admin_site')

        try:
            for i in range(len(pth_lst)):
                pth = pth_lst[i]
                res = requests.get(self.pack_url(path=pth))
                n = '!'
                if res.status_code == 200:
                    n = '+'
                pr(f'({i}/{len(pth_lst)}) "{pth}" code: {fg if res.status_code == 200 else fx}{res.status_code}{fx}', n)
        except requests.exceptions.ConnectionError:
            pr("Couldn't connect!", '!')
