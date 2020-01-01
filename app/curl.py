import pycurl
from io import BytesIO
import re
import logging

# Setup Logging
logger = logging.getLogger('curl.py')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

headers = {}
def header_function(header_line):
    """
    Decode the returned header and store key-value pairs in
    the global dictionary headers
    """

    # HTTP standard specifies that headers are encoded in iso-8859-1
    header_line = header_line.decode('iso-8859-1')

    # Header lines include the first status line (HTTP/1.x ...).
    # We are going to ignore all lines that don't have a colon in them.
    # This will botch headers that are split on multiple lines...
    if ':' not in header_line:
        return

    # Break the header line into header name and value.
    name, value = header_line.split(':', 1)

    # Remove whitespace that may be present.
    # Header lines include the trailing newline, and there may be whitespace
    # around the colon.
    name = name.strip()
    value = value.strip()

    # Header names are case insensitive. Lowercase name here.
    name = name.lower()

    # Now we can actually record the header name and value.
    # Note: this only works when headers are not duplicated.
    headers[name] = value

def curl(url="", iface=None):
    c = pycurl.Curl()
    buffer = BytesIO()

    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.WRITEFUNCTION, buffer.write)
    c.setopt(pycurl.TIMEOUT, 60)
    # Set our header function.
    c.setopt(c.HEADERFUNCTION, header_function)

    if iface:
        c.setopt(pycurl.INTERFACE, iface)
    
    try:
        c.perform()
    except pycurl.error as err:
        # Three errors that need handling:
        # 1. (6, 'Could not resolve host: add-on.ee.co.uk')
        # 2. (28, 'Resolving timed out after xxx milliseconds')
        # 3. (45, "Couldn't bind to 'iface'")
        logger.error(f'Error whilst CURL: {err}')
        resp = None
    else:
        # Figure out what encoding was sent with the response, if any.
        # Check against lowercased header name.
        encoding = None
        if 'content-type' in headers:
            content_type = headers['content-type'].lower()
            match = re.search(r'charset=(\S+)', content_type)
            if match:
                encoding = match.group(1)
                logger.debug(f'Decoding using {encoding}')
        if encoding is None:
            # Default encoding for HTML is iso-8859-1..
            encoding = 'iso-8859-1'
            logger.debug(f'Assuming encoding is {encoding}')
        
        # logger.debug(f'Headers: {headers}')

        resp = buffer.getvalue().decode('iso-8859-1')
    finally:
        buffer.close()
        c.close()   

    return resp


if __name__ == '__main__':
    res = curl('http://add-on.ee.co.uk', "eno1")
    logger.DEBUG(res)
