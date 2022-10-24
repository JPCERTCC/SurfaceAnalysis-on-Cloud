# -*- config:utf-8 -*-
# Reference:
#   https://github.com/oreilly-japan/black-hat-python-2e-ja
#   __author__ = 'Hiroyuki Kakara'


import os
import filetype
import requests
from io import StringIO
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    laparams.detect_vertical = True
    device = TextConverter(rsrcmgr,
        retstr, codec=codec, laparams=laparams)
    with open(path, 'rb') as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        file_str = ''
        try:
            for page in PDFPage.get_pages(fp, set(), maxpages=0, caching=True, check_extractable=True):
                interpreter.process_page(page)
                file_str += retstr.getvalue()
        except Exception as e:
            fp.close()
            device.close()
            retstr.close()
            return -2
    device.close()
    retstr.close()
    return file_str


class get_from_web:
    def get_web_content(self, url):
        try:
            re = requests.get(url, timeout=(3.0, 7.5))
        except Exception as ex:
            return str(ex)
        saveFileName = "/tmp/" + str(datetime.now().timestamp())
        saveFile = open(saveFileName, 'wb')
        saveFile.write(re.content)
        saveFile.close()
        file_type = filetype.guess(saveFileName)
        if file_type is not None and file_type.extension =="pdf":
            pdf_text = convert_pdf_to_txt(saveFileName)
            os.remove(saveFileName)
            return pdf_text
        else:
            try:
                os.remove(saveFileName)
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--hide-scrollbars')
                options.add_argument('--single-process')
                options.add_argument('--ignore-certificate-errors')
                options.add_argument('--no-sandbox')
                options.add_argument('--headless')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--homedir=/tmp')
                options.add_argument('--user-data-dir=/tmp')
                options.add_argument(f'--user-agent={USER_AGENT}')
                options.binary_location = "/opt/python/bin/headless-chromium"
                driver = webdriver.Chrome('/opt/python/bin/chromedriver', chrome_options=options)
                driver.get(url)
                result = driver.page_source.encode('utf-8')
                driver.quit()
                soup = BeautifulSoup(result, "html.parser")
                return soup.get_text()
            except Exception as e:
                print("[!] {0}: get_web_content Exception: {1}".format(datetime.now(), e))
                return -1
