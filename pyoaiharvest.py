import sys
import urllib2
import zlib
import time
import re
import xml.dom.pulldom
import operator
import codecs
from optparse import OptionParser

nDataBytes, nRawBytes, nRecoveries, maxRecoveries = 0, 0, 0, 3


def getFile(serverString, command, verbose=1, sleepTime=0):
    global nRecoveries, nDataBytes, nRawBytes
    if sleepTime:
        time.sleep(sleepTime)
    remoteAddr = serverString + '?verb=%s' % command
    if verbose:
        print "\r", "getFile ...'%s'" % remoteAddr[-90:]
    headers = {'User-Agent': 'OAIHarvester/2.0', 'Accept': 'text/html',
               'Accept-Encoding': 'compress, deflate'}
    try:
        #remoteData=urllib2.urlopen(urllib2.Request(remoteAddr, None, headers)).read()
        remoteData = urllib2.urlopen(remoteAddr).read()
    except urllib2.HTTPError, exValue:
        if exValue.code == 503:
            retryWait = int(exValue.hdrs.get("Retry-After", "-1"))
            if retryWait < 0:
                return None
            print 'Waiting %d seconds' % retryWait
            return getFile(serverString, command, 0, retryWait)
        print exValue
        if nRecoveries < maxRecoveries:
            nRecoveries += 1
            return getFile(serverString, command, 1, 60)
        return
    nRawBytes += len(remoteData)
    try:
        remoteData = zlib.decompressobj().decompress(remoteData)
    except:
        pass
    nDataBytes += len(remoteData)
    mo = re.search('<error *code=\"([^"]*)">(.*)</error>', remoteData)
    if mo:
        print "OAIERROR: code=%s '%s'" % (mo.group(1), mo.group(2))
    else:
        return remoteData

if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option("-l", "--link", dest="link", help="URL of repository")
    parser.add_option("-o", "--filename", dest="filename", help="write repository to file")
    parser.add_option("-f", "--from", dest="fromDate", help="harvest records from this date yyyy-mm-dd")
    parser.add_option("-u", "--until", dest="until", help="harvest records until this date yyyy-mm-dd")
    parser.add_option("-m", "--mdprefix", dest="mdprefix", default="oai_dc", help="use the specified metadata format")
    parser.add_option("-s", "--setName", dest="setName", help="harvest the specified set")

    (options, args) = parser.parse_args()

    if options.link is None or options.filename is None:
        parser.print_help()
        parser.error("a repository url and output file are required")

    if options:
        serverString = verbOpts = fromDate = untilDate = mdPrefix = oaiSet = ''
        if options.link:
            serverString = options.link
        if options.filename:
            outFileName = options.filename
        if options.fromDate:
            fromDate = options.fromDate
        if options.until:
            untilDate = options.until
        if options.mdprefix:
            mdPrefix = options.mdprefix
        if options.setName:
            oaiSet = options.setName
    else:
        print usage

    if not serverString.startswith('http'):
        serverString = 'http://' + serverString

    print "Writing records to %s from archive %s" % (outFileName, serverString)

    ofile = codecs.lookup('utf-8')[-1](file(outFileName, 'wb'))

    ofile.write('<repository xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" \
     xmlns:dc="http://purl.org/dc/elements/1.1/" \
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')  # wrap list of records with this

    if oaiSet:
        verbOpts += '&set=%s' % oaiSet
    if fromDate:
        verbOpts += '&from=%s' % fromDate
    if untilDate:
        verbOpts += '&until=%s' % untilDate
    if mdPrefix:
        verbOpts += '&metadataPrefix=%s' % mdPrefix
    else:
        verbOpts += '&metadataPrefix=%s' % 'oai_dc'

    print "Using url:%s" % serverString + '?ListRecords' + verbOpts

    data = getFile(serverString, 'ListRecords' + verbOpts)

    recordCount = 0

    while data:
        events = xml.dom.pulldom.parseString(data)
        for (event, node) in events:
            if event == "START_ELEMENT" and node.tagName == 'record':
                events.expandNode(node)
                node.writexml(ofile)
                recordCount += 1
        mo = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>', data)
        if not mo:
            break
        data = getFile(serverString, "ListRecords&resumptionToken=%s" % mo.group(1))

    ofile.write('\n</repository>\n'), ofile.close()

    print "\nRead %d bytes (%.2f compression)" % (nDataBytes, float(nDataBytes) / nRawBytes)

    print "Wrote out %d records" % recordCount
