from bs4 import BeautifulSoup
import subprocess
import logging
import datetime
import re
import curl

# Setup Logging
logger = logging.getLogger('ee.py')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


URL = 'http://add-on.ee.co.uk'
INTERFACE = 'enp2s0f0'


class EE:
    def __init__(self, url=URL, interface=INTERFACE):
        self._url = url
        self._interface = interface

    def download(self):
        """ Downloads the EE status page using CURL shell command """
        start_time = datetime.datetime.now()
        resp = curl.curl(url=self._url, iface=self._interface)
        end_time = datetime.datetime.now()
        elapsed_time = end_time - start_time
        self._elapsed_time = round(elapsed_time.seconds * \
                1000 + elapsed_time.microseconds / 1000, 3)
        logger.info(f'Download time {self._elapsed_time}')

        return resp

    def scrape(self):
        """ Scrapes an EE status web page returning a dictionary of data """

        logger.info('Starting ee usage web scraper...')

        raw_html = self.download()

        if raw_html is None:
            self._connected = 'disconnected'
            return self.json()

        self._connected = 'connected'

        # logger.debug(raw_html)
        logger.debug('Parsing HTML using BeautifulSoup')

        parsed_html = BeautifulSoup(raw_html, 'html.parser')

        # find span with the class name 'allowance__left'
        logger.debug('Finding usage info HTML Span')
        spans = parsed_html.find_all(class_='allowance__left')
        if not spans:
            logger.warn('Error finding class=allowance__left span')
            return None

        span = spans[0].get_text()
        logger.debug(f'Found Span {span}')

        # Extract the usage and allowance
        # regex expression to search for 115.5GB or 200GB
        regex = r'\b(\d+[\.]?[\d+]?)([M|G]B)'
        logger.debug(f'Scraping Span leaf text with regex {regex}')

        results = [s for s in re.findall(regex, span)]
        logger.debug(f'    -> result {results}')

        (usage, usage_units), (allowance, allowance_units) = results
        logger.debug(f'    -> received usage: {usage} {usage_units}')
        logger.debug(
            f'    -> received allowance: {allowance} {allowance_units}')

        # usage, allowance = [float(s) for s in re.findall(regex, span)]
        # logger.debug("Successully received usage: %s and allowance: %s",
        #              usage, allowance)

        self._usage = usage
        self._usage_units = usage_units

        self._allowance = allowance
        self._allowance_units = allowance_units

        self._timestamp = datetime.datetime.utcnow().isoformat()

        # Scrape time remaining

        # <p class="allowance__timespan">
        #     Lasts for <span>  <b>9</b> Days  <b>0</b> Hrs
        #     </span>
        # </p>

        paras = parsed_html.find_all(class_='allowance__timespan')
        if not paras:
            logger.warn('Error finding <p class=allowance__timespan>')
            return None
        logger.debug(f'  Found p {paras}')

        time_remaining = paras[0].span.get_text().strip()
        logger.debug(f'    -> time remaining : {time_remaining}')

        #  8 Days  23 Hrs
        regex = r'(\d+)'
        logger.debug('  Scraping Span leaf text with regex {regex}')
        days, hours = [int(s) for s in re.findall(regex, time_remaining)]
        logger.debug(
            f'  -> extracted time remaining: {days} days {hours} hours')

        self._days = days
        self._hours = hours

        return self.json()

    def allowance(self):
        return self._allowance

    def usage(self):
        return self._usage

    def to_GB(self, num, units):
        """ Converts from KB, MB, GB, TB to GB """
        defs = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        bytes = float(num) * defs[units]
        return round(bytes/defs['GB'], 3)

    def json(self):
        """ Creates a dictionary of the instance variables.
            Allowance and usage is converted to standard units. """
        return {
            'timestamp': self._timestamp,
            'usage': self.to_GB(self._usage, self._usage_units),
            'usage_units': 'GB',
            'allowance': self.to_GB(self._allowance, self._allowance_units),
            'allowance_units': 'GB',
            'days_remaining': self._days,
            'hours_remaining': self._hours,
            'download_time_ms': self._elapsed_time,
            'connection_status': self._connected
        }
