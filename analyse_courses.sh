#!/bin/sh
SEMESTERS=$1

export PYTHONPATH=.

echo "Cleaning previous data..."
make clean-analysis

echo "Starting to scrape data..."
make scrape SEMESTERS=$SEMESTERS
echo "Finished scraping data"

echo "Starting to extract data from downloaded files..."
make extract
echo "Finished extracting data"

echo "Cleaning and tokenizing text..."
make tokenize
echo "Finished tokenizing"

echo "Performing LDA analysis"
make analyse
echo "Finished analysing data"
