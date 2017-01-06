#!/bin/sh

export PYTHONPATH=.

function run {
	START_TIME=$SECONDS
	if [ -n "$3" ]
		then
			make $1 $3
		else
			make $1
	fi
	ELAPSED_TIME=$(($SECONDS - $START_TIME))
	mkdir -p -v backup/$1
	cp db/courses.sqlite backup/$1
	echo `date +%Y-%m-%d:%H:%M:%S` $2 in $ELAPSED_TIME seconds >> backup/execution_times.txt
}

function usage {
    echo "usage: analyse_courses [[[-s semesters ] [-m]] | [-h]]"
	echo "	-s, --semesters semesters	comma separated list of semesters to be scraped from courses web page. E.g 2015F,2016S"
	echo "	-m, --moodle			scrape data from moodle"
	echo "	-sis, --studyinfosystem			extract study information system data from .csv file"
	echo "	-h, --help 			display help"
}

SEMESTERS=
MOODLE=
SIS=
while [ "$1" != "" ]; do
    case $1 in
        -s | --semesters )      shift
                                SEMESTERS=$1
                                ;;
        -m | --moodle )    		MOODLE=1
                                ;;
        -sis | --studyinfosystem )    		SIS=1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

echo "Cleaning previous data..."
make clean-analysis

if [ "$SEMESTERS" != "" ]; then
	echo "Starting to scrape data from courses..."
	run scrape-courses "Finished scraping data from courses" "SEMESTERS="$SEMESTERS
else
	echo "Skip scraping data from courses"
fi

if [ "$MOODLE" = "1" ]; then
	echo "Starting to scrape data from moodle..."
	run scrape-moodle "Finished scraping data from moodle"
else
	echo "Skip scraping data from moodle"
fi

if [ "$SIS" = "1" ]; then
	echo "Starting to extract study information system data from file..."
	run extract-sis "Finished extracting SIS data from file" "SEMESTERS="$SEMESTERS
else
	echo "Skip extracting SIS data from file"
fi

echo "Starting to extract data from downloaded files..."
run extract "Finished extracting data"

echo "Cleaning and tokenizing text..."
run tokenize "Finished tokenizing"

echo "Performing LDA analysis"
run analyse "Finished analysing data"
