from html2txt import Html2txt
from pdf2txt import Pdf2Txt
from pptx2txt import Pptx2Txt
import os.path
import sys

if __name__ == '__main__':
    prefix = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\'

    process_count = 7
    if len(sys.argv) == 2:
        process_count = int(sys.argv[0])

    print "Extracting text from html..."
    Html2txt(process_count).extract_text()

    print "Extracting text from pptx files..."
    Pptx2Txt(prefix, process_count).extract_text()

    print "Extracting text from pdf files..."
    Pdf2Txt(prefix, process_count).extract_text()