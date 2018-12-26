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
    echo "usage: analyse_courses [[[-s semesters ] [-sis] [-t] [-tdir] [-m] [-fc]] | [-h]]"
	echo "	-s, --semesters semesters	comma separated list of semesters to be scraped from courses web page. E.g 2015F,2016S"
	echo "	-tdir, --targetdirectory			directory where the resulting DB file will be copied"
	echo "	-fc, --fullclean			remove all existing data including corresponding DB entries. Re-download everything instead of just updating the missing parts"
	echo "	-h, --help 			display help"
	echo "	-cc, --course_code				course code that need to be processed
}

SEMESTERS=
COURSE_CODE=
TARGET_DIR=
FULL_CLEAN=
while [ "$1" != "" ]; do
    case $1 in
        -s | --semesters )      shift
                                SEMESTERS=$1
                                ;;
        -cc | --course_code			shift
        						COURSE_CODE=$1
		-tdir | --targetdirectory )	     shift
								TARGET_DIR=$1
								;;
        -fc | --fullclean )    		FULL_CLEAN=1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

if [ "$FULL_CLEAN" = "1" ]; then
	echo "Removing all previous data..."
	make clean-analysis "fc=1"
else
	echo "Removing current results..."
	make clean-analysis "fc=0"
fi

if [ "$SEMESTERS" != "" && "$COURSE_CODE" != ""]; then
	echo "Starting to scrape data from courses..."
	run scrape-course "Finished scraping data from courses" "SEMESTERS="$SEMESTERS "COURSE_CODE="$COURSE_CODE
else
	echo "Skip scraping data from courses"
fi

if [ "$FULL_CLEAN" = "" ] && [ "$SEMESTERS" != "" ]; then
    echo "Removing stale data..."
    make clean-stale "SEMESTERS="$SEMESTERS
fi

echo "Starting to extract data from downloaded files..."
python -m extraction.TextExtractor "Finished extracting data"

echo "Cleaning and tokenizing text..."
python -m cleaning.Tokenizer "Finished tokenizing"

if [ "$TARGET_DIR" != "" ]; then
	echo "Copying database file to target directory..."
	cp -rf db/courses.sqlite $TARGET_DIR
fi
