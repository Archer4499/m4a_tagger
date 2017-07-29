"""
WPTools Fetch module.
"""

import pycurl
import requests
import sys
import time

from . import __title__, __contact__, __version__
from io import BytesIO
from string import Template


class WPToolsFetch:

    ENDPOINT = "https://en.wikipedia.org"
    QUERY = Template(("${WIKI}/w/api.php?action=parse"
                      "&format=json"
                      "&page=${page}"
                      "&prop=parsetree"
                      "&disablelimitreport="
                      "&disableeditsection="
                      "&disabletoc="
                      "&contentmodel=text"))
    RETRY_SLEEP = 2
    RETRY_MAX = 3
    TIMEOUT = 30

    def __init__(self, wiki=ENDPOINT, lead=False, verbose=False):
        self.wiki = wiki or self.ENDPOINT
        self.lead = lead
        self.verbose = verbose
        self.cobj = self.curl_setup()
        self.title = None
        self.retries = 0

    def __del__(self):
        self.cobj.close()
        if self.verbose:
            print("connection closed.", file=sys.stderr)

    def curl_setup(self):
        crl = pycurl.Curl()
        crl.setopt(crl.USERAGENT, self.user_agent)
        crl.setopt(crl.FOLLOWLOCATION, True)
        crl.setopt(crl.CONNECTTIMEOUT, self.TIMEOUT)
        return crl

    def curl(self, url):
        """speed"""
        crl = self.cobj
        try:
            crl.setopt(crl.URL, url)
        except UnicodeEncodeError:
            crl.setopt(crl.URL, url.encode('utf-8'))
        return self.curl_perform(crl)

    def curl_perform(self, crl):
        """try curl, retry after sleep up to max retries"""
        if self.retries >= self.RETRY_MAX:
            return "RETRY_MAX ({}) exceeded!".format(self.RETRY_MAX)
        try:
            bfr = BytesIO()
            crl.setopt(crl.WRITEFUNCTION, bfr.write)
            crl.setopt(crl.SSL_VERIFYPEER, 0)
            crl.setopt(crl.SSL_VERIFYHOST, 0)
            crl.perform()
            if self.verbose:
                self.curl_report(crl)
            body = bfr.getvalue()
            bfr.close()
            self.retries = 0
            return body.decode(encoding='UTF-8')
        except Exception as detail:
            print("RETRY Caught exception: {}".format(detail))
            self.retries += 1
            time.sleep(self.RETRY_SLEEP)
            self.curl_perform(crl)

    def curl_report(self, crl):
        kbps = crl.getinfo(crl.SPEED_DOWNLOAD) / 1000.0
        out = {"url": crl.getinfo(crl.EFFECTIVE_URL),
               "user-agent": self.user_agent,
               "content": crl.getinfo(crl.CONTENT_TYPE),
               "status": crl.getinfo(crl.RESPONSE_CODE),
               "bytes": crl.getinfo(crl.SIZE_DOWNLOAD),
               "seconds": "{0:5.3f}".format,
               "kB/s": "{0:3.1f}".format(kbps)}
        print("WPToolsFetch HTTP", file=sys.stderr)
        for key in out:
            print("    {0}: {1}".format(key, out[key]), file=sys.stderr)
        print(file=sys.stderr)

    def query(self, page):
        self.title = page
        page = page.replace(" ", "+")
        page = page[0].upper() + page[1:]
        qry = self.QUERY.substitute(WIKI=self.wiki, page=page)
        if self.lead:
            return qry + "&section=0"
        return qry

    #TODO: not used (uses requests lib instead of pycURL)
    def request(self, url, hdr, output):
        print("GET {0}\nHDR {1}\nOUT {2}".format(url, hdr, output), file=sys.stderr)
        r = requests.get(url, headers=hdr, timeout=self.TIMEOUT)
        if r.status_code != 200:
            raise ValueError("HTTP status code = {}".format(r.status_code))
        return r.content

    @property
    def user_agent(self):
        return "{0}/{1} (+{2})".format(__title__, __version__, __contact__)


def get_parsetree(title, lead=False, test=False, wiki=None, verbose=False):
    obj = WPToolsFetch(wiki, lead, verbose)
    qry = obj.query(title)
    if test:
        return qry
    return obj.curl(qry)
