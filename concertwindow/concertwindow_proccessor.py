import itertools
import requests
import sys
from time import sleep
from random import randint
from datetime import datetime

from bs4 import BeautifulSoup


def batches(iterable, n=10):
    """divide a single list into a list of lists of size n """
    batchLen = len(iterable)
    for ndx in range(0, batchLen, n):
        yield list(iterable[ndx:min(ndx + n, batchLen)])


class ConcertWindowProcessor(object):
    def __init__(self, entity, log, retry=3):
        self.log = log
        self.retry = retry
        self.entity = entity
        self.next = None
        self.event_list = []
        self.base_url = "https://www.concertwindow.com"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    def _make_request(self, url, next=None):
        if next:
            url = next
        retries = 0
        while retries <= self.retry:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                self.log.info("{}".format(e))
                sleep(3)
                retries += 1
                if retries <= self.retry:
                    self.log.info("Trying again!")
                    continue
                else:
                    sys.exit("Max retries reached")
            except Exception as e:
                self.log.info("{}: Failed to make request on try {}".format(e, retries))
                retries += 1
                if retries <= self.retry:
                    self.log.info("Trying again!")
                    continue
                else:
                    sys.exit("Max retries reached")

    def _get_events(self):
        self.info = []
        response = self._make_request(self.base_url)
        soup = BeautifulSoup(response.content, "html.parser")
        wrapper = soup.find("ul", attrs={"id": "feed-items"})
        event_list = wrapper.find_all("li")
        for event in event_list:
            a = event.find("a", href=True)
            url = a["href"]
            url = self.base_url + url.replace(" ", "")
            self.info.append(self._get_event_info(url))

    def _get_event_info(self, url):
        event_info = dict()
        response = self._make_request(url)
        soup = BeautifulSoup(response.content, "html.parser")
        artist_name = soup.find("span", attrs={"class": "artist-name"})
        event_name = soup.find("div", attrs={"class": "live-start pbs plxl prxl"})
        event_date = soup.find("div", attrs={"class": "article-top"}).find("h2")
        event_followers = soup.find("span", attrs={"class": "current-followers"})
        event_views = soup.find("span", attrs={"class": "current-page-loads"})
        event_info["date"] = datetime.now().strftime("%Y-%m-%d")
        event_info["artist_name"] = artist_name.text if artist_name else None
        event_info["event_name"] = event_name.text if event_name else None
        event_info["event_date"] = event_date.text.strip() if event_date else None
        event_info["event_followers"] = int(event_followers.text) if event_followers else None
        event_info["event_views"] = int(event_views.text) if event_views else None
        print(event_info)
        return event_info

    def fetch(self):
        self.log.info('Making request to Concertwindow for daily creators export')
        self._get_events()
        return self
