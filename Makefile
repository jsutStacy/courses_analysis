init:
	pip install -r requirements.txt

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +

clean-analysis:
	rm -rf raw_data
	rm -rf backup
	rm -f db/courses.sqlite
	rm -f cleaning/teachers.json
	python db/DataModel.py

scrape-courses:
	scrapy crawl courses -a semesters=$(SEMESTERS)
	
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