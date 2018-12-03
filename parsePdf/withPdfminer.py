
# This works in python 3
# required python packages
# tabula-py==1.0.0
# PyPDF2==1.26.0
# Pillow==4.0.0
# pdfminer.six==20170720

import os
import shutil
import warnings
from io import StringIO

import requests
import tabula
from PIL import Image
from PyPDF2 import PdfFileWriter, PdfFileReader
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

warnings.filterwarnings("ignore")


def download_file(url):
    local_filename = url.split('/')[-1]
    local_filename = local_filename.replace("%20", "_")
    r = requests.get(url, stream=True)
    print(r)
    with open(local_filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    return local_filename


class PDFExtractor():
    def __init__(self, url):
        self.url = url

    # Downloading File in local
    def break_pdf(self, filename, start_page=-1, end_page=-1):
        pdf_reader = PdfFileReader(open(filename, "rb"))
        # Reading each pdf one by one
        total_pages = pdf_reader.numPages
        if start_page == -1:
            start_page = 0
        elif start_page < 1 or start_page > total_pages:
            return "Start Page Selection Is Wrong"
        else:
            start_page = start_page - 1

        if end_page == -1:
            end_page = total_pages
        elif end_page < 1 or end_page > total_pages - 1:
            return "End Page Selection Is Wrong"
        else:
            end_page = end_page

        for i in range(start_page, end_page):
            output = PdfFileWriter()
            output.addPage(pdf_reader.getPage(i))
            with open(str(i + 1) + "_" + filename, "wb") as outputStream:
                output.write(outputStream)

    def extract_text_algo_1(self, file):
        pdf_reader = PdfFileReader(open(file, 'rb'))
        # creating a page object
        pageObj = pdf_reader.getPage(0)

        # extracting extract_text from page
        text = pageObj.extractText()
        text = text.replace("\n", "").replace("\t", "")
        return text

    def extract_text_algo_2(self, file):
        pdfResourceManager = PDFResourceManager()
        retstr = StringIO()
        la_params = LAParams()
        device = TextConverter(pdfResourceManager, retstr, codec='utf-8', laparams=la_params)
        fp = open(file, 'rb')
        interpreter = PDFPageInterpreter(pdfResourceManager, device)
        password = ""
        max_pages = 0
        caching = True
        page_num = set()

        for page in PDFPage.get_pages(fp, page_num, maxpages=max_pages, password=password, caching=caching,
                                      check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()
        text = text.replace("\t", "").replace("\n", "")

        fp.close()
        device.close()
        retstr.close()
        return text

    def extract_text(self, file):
        text1 = self.extract_text_algo_1(file)
        text2 = self.extract_text_algo_2(file)

        if len(text2) > len(str(text1)):
            return text2
        else:
            return text1

    def extarct_table(self, file):

        # Read pdf into DataFrame
        try:
            df = tabula.read_pdf(file, output_format="csv")
        except:
            print("Error Reading Table")
            return

        print("\nPrinting Table Content: \n", df)
        print("\nDone Printing Table Content\n")

    def tiff_header_for_CCITT(self, width, height, img_size, CCITT_group=4):
        tiff_header_struct = '<' + '2s' + 'h' + 'l' + 'h' + 'hhll' * 8 + 'h'
        return struct.pack(tiff_header_struct,
                           b'II',  # Byte order indication: Little indian
                           42,  # Version number (always 42)
                           8,  # Offset to first IFD
                           8,  # Number of tags in IFD
                           256, 4, 1, width,  # ImageWidth, LONG, 1, width
                           257, 4, 1, height,  # ImageLength, LONG, 1, lenght
                           258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
                           259, 3, 1, CCITT_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
                           262, 3, 1, 0,  # Threshholding, SHORT, 1, 0 = WhiteIsZero
                           273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, len of header
                           278, 4, 1, height,  # RowsPerStrip, LONG, 1, lenght
                           279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of extract_image
                           0  # last IFD
                           )

    def extract_image(self, filename):
        number = 1
        pdf_reader = PdfFileReader(open(filename, 'rb'))

        for i in range(0, pdf_reader.numPages):

            page = pdf_reader.getPage(i)

            try:
                xObject = page['/Resources']['/XObject'].getObject()
            except:
                print("No XObject Found")
                return

            for obj in xObject:

                try:

                    if xObject[obj]['/Subtype'] == '/Image':
                        size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                        data = xObject[obj]._data
                        if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                            mode = "RGB"
                        else:
                            mode = "P"

                        image_name = filename.split(".")[0] + str(number)

                        print(xObject[obj]['/Filter'])

                        if xObject[obj]['/Filter'] == '/FlateDecode':
                            data = xObject[obj].getData()
                            img = Image.frombytes(mode, size, data)
                            img.save(image_name + "_Flate.png")
                            # save_to_s3(imagename + "_Flate.png")
                            print("Image_Saved")

                            number += 1
                        elif xObject[obj]['/Filter'] == '/DCTDecode':
                            img = open(image_name + "_DCT.jpg", "wb")
                            img.write(data)
                            # save_to_s3(imagename + "_DCT.jpg")
                            img.close()
                            number += 1
                        elif xObject[obj]['/Filter'] == '/JPXDecode':
                            img = open(image_name + "_JPX.jp2", "wb")
                            img.write(data)
                            # save_to_s3(imagename + "_JPX.jp2")
                            img.close()
                            number += 1
                        elif xObject[obj]['/Filter'] == '/CCITTFaxDecode':
                            if xObject[obj]['/DecodeParms']['/K'] == -1:
                                CCITT_group = 4
                            else:
                                CCITT_group = 3
                            width = xObject[obj]['/Width']
                            height = xObject[obj]['/Height']
                            data = xObject[obj]._data  # sorry, getData() does not work for CCITTFaxDecode
                            img_size = len(data)
                            tiff_header = self.tiff_header_for_CCITT(width, height, img_size, CCITT_group)
                            img_name = image_name + '_CCITT.tiff'
                            with open(img_name, 'wb') as img_file:
                                img_file.write(tiff_header + data)

                            # save_to_s3(img_name)
                            number += 1
                except:
                    continue

        return number

    def read_pages(self, start_page=-1, end_page=-1):

        # Downloading file locally
        downloaded_file = download_file(self.url)
        print(downloaded_file)

        # breaking PDF into number of pages in diff pdf files
        self.break_pdf(downloaded_file, start_page, end_page)

        # creating a pdf reader object
        pdf_reader = PdfFileReader(open(downloaded_file, 'rb'))

        # Reading each pdf one by one
        total_pages = pdf_reader.numPages

        if start_page == -1:
            start_page = 0
        elif start_page < 1 or start_page > total_pages:
            return "Start Page Selection Is Wrong"
        else:
            start_page = start_page - 1

        if end_page == -1:
            end_page = total_pages
        elif end_page < 1 or end_page > total_pages - 1:
            return "End Page Selection Is Wrong"
        else:
            end_page = end_page

        for i in range(start_page, end_page):
            # creating a page based filename
            file = str(i + 1) + "_" + downloaded_file

            print("\nStarting to Read Page: ", i + 1, "\n -----------===-------------")

            file_text = self.extract_text(file)
            print(file_text)
            self.extract_image(file)

            self.extarct_table(file)
            os.remove(file)
            print("Stopped Reading Page: ", i + 1, "\n -----------===-------------")

        os.remove(downloaded_file)


# I have tested on these 3 pdf files
# url = "http://s3.amazonaws.com/NLP_Project/Original_Documents/Healthcare-January-2017.pdf"
url = "http://s3.amazonaws.com/NLP_Project/Original_Documents/Sample_Test.pdf"
# url = "http://s3.amazonaws.com/NLP_Project/Original_Documents/Sazerac_FS_2017_06_30%20Annual.pdf"
# creating the instance of class
pdf_extractor = PDFExtractor(url)

# Getting desired data out
pdf_extractor.read_pages(15, 23)
