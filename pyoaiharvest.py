"""pyoaiharvester script for harvesting OAI-PMH 2.0 Repositories"""

import urllib.request
import zlib
import time
import re
import xml.dom.pulldom
import argparse

N_DATA_BYTES, N_RAW_BYTES, N_RECOVERIES, MAX_RECOVERIES = 0, 0, 0, 3


def get_file(server_string, command, verbose=1, sleep_time=0):
    """Primary function for requesting OAI-PMH data from repository,
       checking for errors, handling possible compression and returning
       the XML string to the rest of the script for writing to a file."""

    global N_RECOVERIES, N_DATA_BYTES, N_RAW_BYTES
    if sleep_time:
        time.sleep(sleep_time)
    remote_addr = server_string + f'?verb={command}'
    if verbose:
        print("\r", f"get_file ...'{remote_addr[-90:]}'")
    headers = {'User-Agent': 'pyoaiharvester/3.0', 'Accept': 'text/html',
               'Accept-Encoding': 'compress, deflate'}
    try:
        req = urllib.request.Request(remote_addr, headers=headers)
        with urllib.request.urlopen(req) as response:
            remote_data = response.read()
    except urllib.request.HTTPError as ex_value:
        if ex_value.code == 503:
            retry_wait = int(ex_value.hdrs.get("Retry-After", "-1"))
            if retry_wait < 0:
                return None
            print(f'Waiting {retry_wait} seconds')
            return get_file(server_string, command, 0, retry_wait)
        if N_RECOVERIES < MAX_RECOVERIES:
            N_RECOVERIES += 1
            return get_file(server_string, command, 1, 60)
        return None
    N_RAW_BYTES += len(remote_data)
    try:
        remote_data = zlib.decompressobj().decompress(remote_data)
    except zlib.error:
        pass
    remote_data = remote_data.decode('utf-8')
    N_DATA_BYTES += len(remote_data)
    error_code = re.search('<error *code=\"([^"]*)">(.*)</error>', remote_data)
    if error_code:
        print(f"OAIERROR: code={error_code.group(1)} '{error_code.group(2)}'")
        return None

    return remote_data

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--link", dest="link",
                        help="URL of repository")
    parser.add_argument("-o", "--filename", dest="filename",
                        help="write repository to file")
    parser.add_argument("-f", "--from", dest="from_date",
                        help="harvest records from this date yyyy-mm-dd")
    parser.add_argument("-u", "--until", dest="until",
                        help="harvest records until this date yyyy-mm-dd")
    parser.add_argument("-m", "--mdprefix", dest="md_prefix", default="oai_dc",
                        help="use the specified metadata format")
    parser.add_argument("-s", "--setName", dest="setName",
                        help="harvest the specified set")

    args = parser.parse_args()

    if args.link is None or args.filename is None:
        parser.print_help()
        parser.error("a repository url and output file are required")

    if args:
        SERVER_STRING = VERB_OPTS = FROM_DATE = UNTIL_DATE = MD_PREFIX = OAI_SET = ''
        if args.link:
            SERVER_STRING = args.link
        if args.filename:
            outFileName = args.filename
        if args.from_date:
            FROM_DATE = args.from_date
        if args.until:
            UNTIL_DATE = args.until
        if args.md_prefix:
            MD_PREFIX = args.md_prefix
        if args.setName:
            OAI_SET = args.setName
    else:
        parser.print_help()

    if not SERVER_STRING.startswith('http'):
        SERVER_STRING = 'https://' + SERVER_STRING

    print(f"Writing records to {outFileName} from archive {SERVER_STRING}")

    if OAI_SET:
        VERB_OPTS += f'&set={OAI_SET}'
    if FROM_DATE:
        VERB_OPTS += f'&from={FROM_DATE}'
    if UNTIL_DATE:
        VERB_OPTS += f'&until={UNTIL_DATE}'

    VERB_OPTS += f'&metadataPrefix={MD_PREFIX}'  # Defaults to oai_dc

    print(f"Using url:{SERVER_STRING + '?ListRecords' + VERB_OPTS}")

    with open(outFileName, "w", encoding="utf-8") as ofile:
        ofile.write('<repository xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" \
     xmlns:dc="http://purl.org/dc/elements/1.1/" \
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')

        data = get_file(SERVER_STRING, 'ListRecords' + VERB_OPTS)

        RECORD_COUNT = 0

        while data:
            events = xml.dom.pulldom.parseString(data)
            for (event, node) in events:
                if event == "START_ELEMENT" and node.tagName == 'record':
                    events.expandNode(node)
                    node.writexml(ofile)
                    RECORD_COUNT += 1
            mo = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>', data)
            if not mo:
                break
            data = get_file(SERVER_STRING, f"ListRecords&resumptionToken={mo.group(1)}")

        ofile.write('\n</repository>\n')
        ofile.close()

    print(f"\nRead {N_DATA_BYTES} bytes ({N_DATA_BYTES / N_RAW_BYTES:.2f} compression)")

    print(f"Wrote out {RECORD_COUNT:,d} records")
