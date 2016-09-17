init:
	pip install -r requirements.txt

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +

clean-analysis:
	rm -rf raw_data
	rm -f db/courses.sqlite
	python db/DataModel.py

scrape:
	scrapy crawl courses -a semesters=$(SEMESTERS)

extract:
	python extraction/TextExtractor.py

tokenize:
	python cleaning/tokenizer.py

analyse:
	python analysis/topicmodeling.py