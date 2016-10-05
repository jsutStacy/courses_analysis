from html2txt import Html2txt
from pdf2txt import Pdf2Txt
from pptx2txt import Pptx2Txt
from docx2txt import Docx2txt
from db.DataModel import db, Course, Lecture
from scraping.spiders.CoursesSpider import CoursesSpider
import os.path
import sys
import peewee


def __remove_duplicates():
    """
    Removes all duplicate material within the scope of a single course.
    Currently duplicate detection works based on material name, i.e if
    the names without extensions match, we remove one of the duplicates
    (preferably the .pdf one, since extracting text from pdf is more
    prone to errors).
    """
    lectures_to_delete = []

    for course in Course.select().where(Course.id == 2):
        lectures = {}
        for lecture in Lecture.select().where(Lecture.course == course):
            extension = __resolve_extension(lecture.name)
            if not extension:
                continue

            pure_name = lecture.name[:-len(extension)]  # Get lecture name without extension
            if pure_name in lectures:
                existing = lectures[pure_name]

                if existing.name.endswith('.pdf'):  # Prefer anything to .pdf extension
                    lectures_to_delete.append(existing)
                    lectures[pure_name] = lecture
                else:
                    lectures_to_delete.append(lecture)
            else:
                lectures[pure_name] = lecture  # Initial insert
    try:
        with db.transaction():
            for lecture in lectures_to_delete:
                lecture.delete_instance()
    except peewee.OperationalError as e:
        print e


def __resolve_extension(word):
    res = ""
    for extension in CoursesSpider.allowed_extensions:
        if word.endswith(extension):
            res = extension
            break
    return res

if __name__ == '__main__':
    prefix = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '\\'

    process_count = 7
    if len(sys.argv) == 2:
        process_count = int(sys.argv[1])

    print "Removing duplicate materials..."
    __remove_duplicates()

    print "Extracting text from html..."
    Html2txt(process_count).extract_text()

    print "Extracting text from pptx files..."
    Pptx2Txt(prefix, process_count).extract_text()

    print "Extracting text from docx files..."
    Docx2txt(prefix, process_count).extract_text()

    print "Extracting text from pdf files..."
    Pdf2Txt(prefix, process_count).extract_text()