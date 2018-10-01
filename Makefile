init:
	pip install -r requirements.txt

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +
	
clean-stale:
	python db/CleanDatabase.py $(SEMESTERS)
	find ./raw_data -type d -empty -delete	

clean-analysis:
ifeq ($(fc),1)
	rm -rf raw_data
	rm -f db/courses.sqlite
endif
	rm -rf backup
	rm -f cleaning/teachers.json
	python db/DataModel.py

scrape-courses:
	scrapy crawl courses -a semesters=$(SEMESTERS)

scrape-course:
	scrapy crawl courses -a semesters=$(SEMESTERS) -a course_code=$(COURSE_CODE)
	
scrape-moodle:
	scrapy crawl moodle

scrape-teachers:
	scrapy crawl teacher -o cleaning/teachers.json

extract-sis:
	python extraction/SisDataLoader.py $(SEMESTERS)

extract:
	python extraction/TextExtractor.py

tokenize:
	python cleaning/Tokenizer.py

analyse:
	python analysis/TopicModeling.py