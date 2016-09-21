from html2txt import Html2txt
from pdf2txt import Pdf2Txt
from pptx2txt import Pptx2Txt
import os.path

if __name__ == '__main__':
    prefix = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\'

    print "Extracting text from html..."
    Html2txt().extract_text()

    print "Extracting text from pptx files..."
    Pptx2Txt(prefix).extract_text()

    print "Extracting text from pdf files..."
    Pdf2Txt(prefix).extract_text()