#!/bin/sh
SEMESTERS=$1

export PYTHONPATH=.

function run {
	START_TIME=$SECONDS
	make $1
	ELAPSED_TIME=$(($SECONDS - $START_TIME))
	mkdir -p -v backup/$1
	cp db/courses.sqlite backup/$1
	echo `date +%Y-%m-%d:%H:%M:%S` $2 in $ELAPSED_TIME seconds >> backup/execution_times.txt
}

echo "Cleaning previous data..."
make clean-analysis

echo "Starting to scrape data..."
run "scrape SEMESTERS="$SEMESTERS 'Finished scraping data'

echo "Starting to extract data from downloaded files..."
run extract "Finished extracting data"

echo "Cleaning and tokenizing text..."
run tokenize "Finished tokenizing"

echo "Performing LDA analysis"
run analyse "Finished analysing data"
