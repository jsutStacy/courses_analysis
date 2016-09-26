#!/bin/sh
SEMESTERS=$1

export PYTHONPATH=.

function backup {
	mkdir -p -v backup/$1
	cp db/courses.sqlite backup/$1
}

echo "Cleaning previous data..."
make clean-analysis

echo "Starting to scrape data..."
make scrape SEMESTERS=$SEMESTERS
backup scrape
echo "Finished scraping data"

echo "Starting to extract data from downloaded files..."
make extract
backup extract
echo "Finished extracting data"

echo "Cleaning and tokenizing text..."
make tokenize
backup tokenize
echo "Finished tokenizing"

echo "Performing LDA analysis"
make analyse
backup analyse
echo "Finished analysing data"
