import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from db.DataModel import Lecture, db
from pdfminer.pdftypes import PDFException
from pdfminer.pdfparser import PDFSyntaxError
import pathos.multiprocessing as mp
import peewee
import os.path


class Pdf2Txt(object):
    def __init__(self, prefix, process_count=8):
        self.prefix = prefix
        self.caching = True
        self.codec = 'utf-8'
        self.laparams = LAParams()
        self.imagewriter = None
        self.pagenos = set()
        self.maxpages = 0
        self.password = ''
        self.rotation = 0
        self.pool = mp.ProcessingPool(process_count)

    def __convert(self, lecture, ofile=None):
        path = self.prefix + lecture.path
        if not os.path.exists(path):
            print "File not found: {0}".format(path)
            return
        print lecture.url

        fp = file(path, 'rb')

        if ofile is None:
            outfp = StringIO.StringIO()
        else:
            outfp = file(ofile, 'wb')

        rsrcmgr = PDFResourceManager(caching=self.caching)
        device = TextConverter(rsrcmgr, outfp, codec=self.codec, laparams=self.laparams,
                               imagewriter=self.imagewriter)

        interpreter = PDFPageInterpreter(rsrcmgr, device)

        try:
            for page in PDFPage.get_pages(
                    fp, self.pagenos,
                    maxpages=self.maxpages, password=self.password,
                    caching=self.caching, check_extractable=True):
                page.rotate = (page.rotate + self.rotation) % 360
                interpreter.process_page(page)
        except (PDFException, MemoryError, PDFSyntaxError, ValueError) as e:
            print "Could not extract text {0}".format(e)

        fp.close()
        device.close()
        retval = None
        if ofile is None:
            retval = outfp.getvalue()

        outfp.close()

        lecture.content = retval
        return lecture

    def extract_text(self):
        lectures = Lecture.select().where(Lecture.content == '', Lecture.url % "*pdf")

        result_lectures = self.pool.map(self.__convert, lectures)

        for lecture in result_lectures:
            if lecture:
                try:
                    with db.transaction():
                        lecture.save()
                except peewee.OperationalError as e:
                    print e