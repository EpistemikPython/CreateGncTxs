#!/usr/bin/env python

# parsePdf.py -- parse a PDF file and recover the text
#
# Copyright (c) 2018, 2019 Mark Sattolo <epistemik@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# @author Mark Sattolo <epistemik@gmail.com>

__updated__ = "2019-01-01 17:01"

from sys import argv, exit
import collections
import json
import PyPDF2

def getPage(readPdf, pageNum):
    page = readPdf.getPage(pageNum)
    page_content = page.extractText()
    print("content of page #{0}:".format(sys.argv[1]))
    print page_content.encode('utf-8')
    
def getAllPages(readPdf):
    c = collections.Counter(range(readPdf.getNumPages()))
    for i in c:
       page = readPdf.getPage(i)
       page_content = page.extractText()
       print page_content.encode('utf-8')
    
def main():
    print("len(argv) = {0}".format(len(argv)))
    if len(argv) < 2:
        print("Usage: python '{}' <reportPath> [pageNum]".format(argv[0]))
        exit()
     
    monarch = argv[1]
    print("Monarch report is: {}".format(monarch))
    
    pageNum = 0
    readAll = True
    if len(argv) > 2:
        pageNum = int(argv[2]) - 1
        readAll = False
    
    pdfFile = open(monarch, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFile)
    
    docInfo = pdfReader.getDocumentInfo()
    print("docInfo = {0}".format(json.dumps(docInfo)))
    print("number of pages = {0}".format(pdfReader.getNumPages()))
    
    if readAll:
        getAllPages(pdfReader)
    else:
        getPage(pdfReader, pageNum)
        
    print("Bye!\n")
    
if __name__ == "__main__":
    main()
