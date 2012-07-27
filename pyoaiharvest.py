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
    remoteAddr = serverString+'?verb=%s'%command
    if verbose: 
        print "\r", "getFile ...'%s'"%remoteAddr[-90:]
    headers = {'User-Agent': 'OAIHarvester/2.0', 'Accept': 'text/html',
               'Accept-Encoding': 'compress, deflate'}
    try:
        #remoteData=urllib2.urlopen(urllib2.Request(remoteAddr, None, headers)).read()
        remoteData=urllib2.urlopen(remoteAddr).read()
    except urllib2.HTTPError, exValue:
        if exValue.code==503:
            retryWait = int(exValue.hdrs.get("Retry-After", "-1"))
            if retryWait<0: return None
            print 'Waiting %d seconds'%retryWait
            return getFile(serverString, command, 0, retryWait)
        print exValue
        if nRecoveries<maxRecoveries:
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
        print "OAIERROR: code=%s '%s'"%(mo.group(1), mo.group(2))
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
        serverString=verbOpts=fromDate=untilDate=mdPrefix=oaiSet=''
        if options.link:
            serverString = options.link
        if options.filename:
            outFileName= options.filename
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

    
    if serverString.find('http://')!=0:
        serverString = 'http://'+serverString
    
    print "Writing records to %s from archive %s"%(outFileName, serverString)
    
    ofile = codecs.lookup('utf-8')[-1](file(outFileName, 'wb'))
    
    ofile.write('<repository xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" \
     xmlns:dc="http://purl.org/dc/elements/1.1/" \
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instanc">\n')  # wrap list of records with this
    
    if oaiSet:
        verbOpts+='&set=%s'%oaiSet
    if fromDate:
        verbOpts+='&from=%s'%fromDate
    if untilDate:
        verbOpts+='&until=%s'%untilDate
    if mdPrefix:
        verbOpts+='&metadataPrefix=%s'%mdPrefix
    else:
        verbOpts+='&metadataPrefix=%s'%'oai_dc'
    
    print "Using url:%s"%serverString+'?ListRecords'+verbOpts
        
    data = getFile(serverString, 'ListRecords'+verbOpts)
    
    recordCount = 0
    
    while data:
        events = xml.dom.pulldom.parseString(data)
        for (event, node) in events:
            if event=="START_ELEMENT" and node.tagName=='record':
                events.expandNode(node)
                node.writexml(ofile)
                recordCount += 1
        mo = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>', data)
        if not mo: break
        data = getFile(serverString, "ListRecords&resumptionToken=%s"%mo.group(1))
    
    ofile.write('\n</repository>\n'), ofile.close()
    
    print "\nRead %d bytes (%.2f compression)"%(nDataBytes, float(nDataBytes)/nRawBytes)
    
    print "Wrote out %d records"%recordCount
    

## Copyright (c) 2000-2003 OCLC Online Computer Library Center, Inc. and other contributors.
## All rights reserved.  The contents of this file, as updated from time to time by the OCLC
## Office of Research are subject to OCLC Research Public License Version 2.0 (the
## "License"); you may not use this file except in compliance with the License.  You may
## obtain a current copy of the License at http://purl.oclc.org/oclc/research/ORPL/.
## Software distributed under the License is distributed on an "AS IS" basis, WITHOUT
## WARRANTY OF ANY KIND, either express or implied.  See the License for the specific
## language governing rights and limitations under the License.  This software consists of
## voluntary contributions made by many individuals on behalf of OCLC Research.  For more
## information on OCLC Research, please see http://www.oclc.org/research/.  This is the
## Original Code.  The Initial Developer of the Original Code is Thomas Hickey
## (mailto:hickey@oclc.org). Portions created by OCLC are Copyright (C) 2003.  All Rights
## Reserved. 2003 July 31a
