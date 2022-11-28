#!/usr/bin/env python3
import logging
import os

from src.domainator import Domainator
from src.utils import pr, choose

if not os.path.isdir('./logs'):
    os.mkdir('./logs')
logging.basicConfig(filename='./logs/log.log',
                    filemode='w', level=logging.DEBUG)
logger = logging.getLogger('chardet.charsetprober')
logger.setLevel(logging.INFO)


def passive_menu(dom: Domainator):
    while 1:
        cc = choose(['Whois Lookup', 'Reverse IP Lookup'])
        if cc < 0:
            break
        elif cc == 0:
            dom.whois()
        elif cc == 1:
            while 1:
                ccc = choose(['HackerTarget', 'YouGetSignal'],
                             'Choose method:')
                if ccc < 0:
                    break
                elif ccc == 0:
                    dom.reverse_HT()
                elif ccc == 1:
                    dom.reverse_YGS()


def active_menu(dom: Domainator):
    while 1:
        cc = choose(
            ['Grab Headers & CloudFlare', 'Site Speed Check',
             'Sub-domains Scan', 'Links Crawler', 'Admin Panel Search'])
        if cc < 0:
            break
        if cc == 0:
            dom.banners_cloud_flare()
        elif cc == 1:
            dom.speed_check()
        elif cc == 2:
            dom.find_subdomains()
        elif cc == 3:
            dom.crawler.menu()
        elif cc == 4:
            dom.find_panels()


def main_menu(dom: Domainator):
    while 1:
        c = choose(['Passive', 'Active'], 'Choose category:')
        if c < 0:
            break
        if c == 0:
            passive_menu(dom)
        if c == 1:
            active_menu(dom)


if __name__ == '__main__':
    logging.info('Starting')
    try:
        main_menu(Domainator())
    except KeyboardInterrupt:
        pr('Interrupted!', '!')
