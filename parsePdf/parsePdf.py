#
# parsePdf.py -- parse a PDF file and recover the text
#
# Copyright (c) 2018,2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018-12
# @updated 2019-04-28

from sys import argv, exit
import os.path as osp
import collections
import json
from datetime import datetime as dt
import PyPDF2
from Configuration import *

now = dt.now().strftime("%Y-%m-%dT%H-%M-%S")


# noinspection PyPep8
def get_page(read_pdf, page_num):
    page = read_pdf.getPage(page_num)
    page_content = page.extractText()
    print_info("content of page #{}:".format(page_num+1), BLUE)
    print_info(page_content.encode('utf-8'), GREEN)


def get_all_pages(pdf_reader, fp):
    c = collections.Counter(range(pdf_reader.getNumPages()))
    for i in c:
        page = pdf_reader.getPage(i)
        page_text = page.extractText()
        # fix Python 2 to Python 3
        # CANNOT change page text to utf-8 with Python 3 or lose newlines...
        # page_content = page_text.encode('utf-8')
        print_info(page_text, BLUE)
        fp.write(page_text)


def parse_pdf_main():
    exe = argv[0].split('/')[-1]
    print_info("len(argv) = {}".format(len(argv)))
    if len(argv) < 2:
        print_error("Usage: python {} <pdf_input_path> [page_num]".format(exe))
        exit()

    monarch = argv[1]
    print_info("Monarch report is: {}".format(monarch), MAGENTA)

    page_num = 0
    read_all = True
    if len(argv) > 2:
        page_num = int(argv[2]) - 1
        read_all = False

    # parse an external Monarch pdf report file
    pdf_file = open(monarch, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)

    doc_info = pdf_reader.getDocumentInfo()
    print_info("doc_info = {0}".format(json.dumps(doc_info)), BLUE)
    print_info("number of pages = {0}".format(pdf_reader.getNumPages()), CYAN)

    # print info as txt file
    # pluck path and basename from pdf file name to use for the saved file
    (path, fname) = osp.split(monarch)
    # print_info("path is '{}'".format(path))

    # save to the output folder
    path = path.replace('in', 'out')
    (basename, ext) = osp.splitext(fname)
    # add a timestamp to get a unique file name
    out_file = path + '/' + basename + '.' + now + '.txt'
    print_info("out_file is '{}'".format(out_file), GREEN)
    fp = open(out_file, 'w')

    if read_all:
        get_all_pages(pdf_reader, fp)
    else:
        get_page(pdf_reader, page_num)

    fp.close()

    print_info("\n >>> PROGRAM ENDED.", CYAN)


if __name__ == "__main__":
    parse_pdf_main()
