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

from __future__ import print_function

__updated__ = "2019-01-26 07:53"

from sys import argv, exit
import collections
import json
import PyPDF2


def get_page(read_pdf, page_num):
    page = read_pdf.getPage(page_num)
    page_content = page.extractText()
    print("content of page #{0}:".format(argv[1]))
    print( page_content.encode('utf-8') )


def get_all_pages(read_pdf):
    c = collections.Counter(range(read_pdf.getNumPages()))
    for i in c:
        page = read_pdf.getPage(i)
        page_content = page.extractText()
        print( page_content.encode('utf-8') )


def parse_pdf_main():
    print("len(argv) = {0}".format(len(argv)))
    if len(argv) < 2:
        print("Usage: python '{}' <reportPath> [page_num]".format(argv[0]))
        exit()

    monarch = argv[1]
    print("Monarch report is: {}".format(monarch))

    page_num = 0
    read_all = True
    if len(argv) > 2:
        page_num = int(argv[2]) - 1
        read_all = False

    pdf_file = open(monarch, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)

    doc_info = pdf_reader.getDocumentInfo()
    print("doc_info = {0}".format(json.dumps(doc_info)))
    print("number of pages = {0}".format(pdf_reader.getNumPages()))

    if read_all:
        get_all_pages(pdf_reader)
    else:
        get_page(pdf_reader, page_num)

    print("Bye!\n")


if __name__ == "__main__":
    parse_pdf_main()
