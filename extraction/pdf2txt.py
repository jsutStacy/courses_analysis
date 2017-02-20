import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from db.DataModel import Lecture, db
import pathos.multiprocessing as mp
import multiprocessing
import peewee
import os.path


class Pdf2Txt(object):
    def __init__(self, prefix, process_count=multiprocessing.cpu_count()*2):
        self.prefix = prefix
        self.pool = mp.ProcessingPool(process_count)
        print "Process count in pool: {} ".format(process_count)

    def __convert(self, lecture):
        path = self.prefix + lecture.path
        if not os.path.exists(path):
            print "File not found: {}".format(path)
            return None
        print lecture.url

        input_file = file(path, 'rb')
        output = StringIO.StringIO()

        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output, codec='utf-8', laparams=LAParams())

        interpreter = PDFPageInterpreter(rsrcmgr, device)

        try:
            for page in PDFPage.get_pages(input_file):
                interpreter.process_page(page)
        except Exception as e:
            print "Could not extract text {}".format(e)

        input_file.close()
        device.close()
        lecture.content = output.getvalue()
        output.close()

        return lecture

    def extract_text(self):
        lectures = Lecture.select().where(Lecture.content == '', Lecture.url % "*pdf")

        result_lectures = self.pool.map(self.__convert, lectures)

        print "PDF extraction complete, processed {} entries".format(len(result_lectures))
        for lecture in result_lectures:
            if lecture:
                try:
                    with db.transaction():
                        lecture.save()
                except peewee.OperationalError as e:
                    print e