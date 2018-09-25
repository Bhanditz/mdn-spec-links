#!/usr/bin/env python2
import certifi
import io
import json
import os.path
import sys
import time
import urllib3
from HTMLParser import HTMLParser
from collections import OrderedDict
from urlparse import urlparse


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def stripTags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def main():
    specs = dict()
    filenames = dict()
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                               ca_certs=certifi.where())

    def getAdjustedData(spec_id, url, path, base_url, hostname, fragment):
        if 'spec.whatwg.org' in hostname:
            path = '/' + hostname.split('.')[0] + '/'
            spec_id = fragment
            if url.startswith('https://html.spec.whatwg.org/multipage/'):
                base_url = 'https://html.spec.whatwg.org/multipage/'
        elif url.startswith('https://tools.ietf.org/html/'):
            name = spec_id.split('#')[0]
            path = '/' + name + '/'
            spec_id = fragment
            base_url = 'https://tools.ietf.org/html/' + name
        elif url.startswith('https://tools.ietf.org/id/'):
            name = spec_id.split('#')[0][:-5]
            path = '/' + name + '/'
            spec_id = fragment
            base_url = 'https://tools.ietf.org/id/' + name
        return spec_id, path, base_url

    def getSpecShortnameAndSpecID(url):
        if '##' in url:
            url = url.replace('##', '#')
        hostname = urlparse(url).hostname
        path = urlparse(url).path
        if path == '':
            base_url = url.split('#')[0]
        else:
            base_url = os.path.dirname(url.split('#')[0])
        base_url = base_url + '/'
        fragment = urlparse(url).fragment
        filename = path.split('/')[-1]
        if filename != '':
            spec_id = filename + '#' + fragment
        else:
            spec_id = fragment
        spec_id, path, base_url = \
            getAdjustedData(spec_id, url, path, base_url, hostname, fragment)
        shortname = os.path.dirname(path).split('/')[-1].lower()
        if base_url in filenames:
            shortname = filenames[base_url][:-5]
        else:
            filenames[base_url] = shortname + '.json'
        if shortname not in specs:
            specs[shortname] = dict()
        return shortname, spec_id

    def getMdnSlug(mdn_url):
        if mdn_url.startswith('https://developer.mozilla.org/docs/Web/'):
            mdn_url = mdn_url[39:]
        else:
            sys.stderr.write('Odd MDN URL: %s\n' % mdn_url)
        return mdn_url

    def addSpecLink(shortname, spec_id, slug, title, summary, support):
        article_details = {}
        article_details['slug'] = slug
        article_details['summary'] = summary
        article_details['support'] = support
        article_details['title'] = title
        if spec_id not in specs[shortname]:
            specs[shortname][spec_id] = []
        specs[shortname][spec_id].append(article_details)

    def isBrokenURL(spec_url):
        return (not(urlparse(spec_url).hostname) or
                ('#' not in spec_url) or
                ('http://' in urlparse(spec_url).path) or
                ('http://' in urlparse(spec_url).fragment))

    def processSpecURL(spec_url, bcd_feature_data):
        if isBrokenURL(spec_url):
            return
        if 'mdn_url' not in bcd_feature_data:
            return
        support = bcd_feature_data['support']
        mdn_url = bcd_feature_data['mdn_url']
        mdn_json_url = 'https://developer.mozilla.org' \
            + urlparse(mdn_url).path + '$json'
        print 'Getting data for %s' % mdn_url
        response = http.request('GET', mdn_json_url)
        if response.status == 404:
            sys.stderr.write('No MDN article at %s\n' % mdn_url)
            return
        if response.status > 499:
            sys.stderr.write('50x for %s. Retrying in 60s...\n' % mdn_url)
            time.sleep(61)
            print 'Retrying %s' % mdn_url
            response = http.request('GET', mdn_json_url)
            if response.status == 404:
                sys.stderr.write('No MDN article at %s\n' % mdn_url)
                return
            if response.status > 499:
                sys.stderr.write('50x for %s. Giving up.\n' % mdn_url)
                return
        mdn_data = json.loads(response.data, object_pairs_hook=OrderedDict)
        slug = getMdnSlug(mdn_url)
        title = mdn_data['title']
        summary = mdn_data['summary']
        summary = stripTags(summary) \
            .encode('utf-8').replace('\xc2\xa0', ' ')
        shortname, spec_id = getSpecShortnameAndSpecID(spec_url)
        addSpecLink(shortname, spec_id, slug, title, summary, support)

    def processDataFromBCD(feature):
        if not('__compat' in feature and 'spec_url' in feature['__compat']):
            return
        bcd_feature_data = feature['__compat']
        if bcd_feature_data['status']['deprecated']:
            return
        if not isinstance(bcd_feature_data['spec_url'], list):
            # spec_url value is a string
            processSpecURL(bcd_feature_data['spec_url'], bcd_feature_data)
            return
        # spec_url value is an array
        for spec_url in bcd_feature_data['spec_url']:
            processSpecURL(spec_url, bcd_feature_data)

    def processLocalItemData(item_data, spec_id, shortname):
        slug = item_data['slug']
        url = 'https://developer.mozilla.org/en-US/docs/Web/' + slug + '$json'
        response = http.request('GET', url)
        if response.status == 404:
            sys.stderr.write('fatal: no MDN article at %s' % url)
            sys.exit(1)
        mdn_data = json.loads(response.data, object_pairs_hook=OrderedDict)
        title = mdn_data['title']
        summary = stripTags(mdn_data['summary']) \
            .encode('utf-8').replace('\xc2\xa0', ' ')
        support = {}
        if 'support' not in item_data:
            addSpecLink(shortname, spec_id, slug, title, summary, support)
            return
        level = item_data['support'].split('.')
        depth = len(level)
        if depth > 2 and level[1] == 'elements':
            filename = ('browser-compat-data/%s/%s/%s.json' %
                        (level[0], level[1], level[2]))
        else:
            filename = ('browser-compat-data/%s/%s.json' %
                        (level[0], level[1]))
        f = io.open(filename, 'r', encoding='utf-8')
        bcd = json.load(f, object_pairs_hook=OrderedDict)
        f.close()
        base = {}
        if depth == 2:
            base = bcd[level[0]][level[1]]
        elif depth == 3:
            base = bcd[level[0]][level[1]][level[2]]
        elif depth == 4:
            base = bcd[level[0]][level[1]][level[2]][level[3]]
        support = base['__compat']['support']
        addSpecLink(shortname, spec_id, slug, title, summary, support)

    def processLocalData(shortname):
        try:
            f = open('.local/' + shortname + '.json', 'rb')
            data = json.load(f, object_pairs_hook=OrderedDict)
            for spec_id in data:
                for item_data in data[spec_id]:
                    processLocalItemData(item_data, spec_id, shortname)
        except IOError:
            pass

    f = io.open('SPECMAP.json', 'r', encoding='utf-8')
    filenames = json.load(f, object_pairs_hook=OrderedDict)
    f.close()
    dirnames = \
        [
            'api',
            'css',
            'html',
            'http',
            'javascript',
            'mathml',
            'svg',
            'webdriver',
            'webextensions',
            'xpath',
            'xslt'
        ]
    for dirname in dirnames:
        files = [os.path.join(dirpath, filename)
                 for (dirpath, dirs, files)
                 in os.walk('browser-compat-data/' + dirname)
                 for filename in (dirs + files)]
        files.sort()
        for filename in files:
            if os.path.splitext(filename)[1] != '.json':
                continue
            f = io.open(filename, 'r', encoding='utf-8')
            json_data = json.load(f, object_pairs_hook=OrderedDict)
            f.close()
            for section_name in json_data:
                for base_name in json_data[section_name]:
                    base_data = json_data[section_name][base_name]
                    processDataFromBCD(base_data)
                    for feature_name in base_data:
                        feature_data = base_data[feature_name]
                        processDataFromBCD(feature_data)
                        for subfeature_name in feature_data:
                            subfeature_data = feature_data[subfeature_name]
                            processDataFromBCD(subfeature_data)

    f = open('SPECMAP.json', 'wb')
    f.write(json.dumps(filenames, sort_keys=True, indent=4,
                       separators=(',', ': ')))
    f.write('\n')
    f.close()
    for shortname in specs:
        processLocalData(shortname)
        f = open(shortname + '.json', 'wb')
        f.write(json.dumps(specs[shortname], sort_keys=True, indent=4,
                           separators=(',', ': ')))
        f.write('\n')
        f.close()

main()
