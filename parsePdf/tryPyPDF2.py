#!/usr/bin/env python

import sys
import collections
import json
import PyPDF2

monarch = "/home/marksa/Downloads/ClientTransactionsReport.pdf"

def main():
    print("len(sys.argv) = {0}".format(len(sys.argv)))
    pageNum = 0
    readAll = True
    if len(sys.argv) > 1:
        pageNum = int(sys.argv[1]) - 1
        readAll = True
        
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

if __name__ == "__main__":
    main()
