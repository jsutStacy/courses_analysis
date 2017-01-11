import datetime


def determine_semester():
    now = datetime.datetime.now()
    semester = 'spring' if 1 < now.month < 9 else 'fall'
    year = now.year - 1 if now.month == 1 else now.year
    return {'year': year, 'semester': semester}


def parse_semesters(semesters_str):
    semesters = set()
    for sem in semesters_str.split(","):
        if len(sem) != 5:
            print "Invalid parameter length, expected 5, actual: {}".format(len(sem))
            continue

        season = sem[-1].upper()
        if season == 'F':
            season = 'fall'
        elif season == 'S':
            season = "spring"
        else:
            print "Invalid semester, expected either F or S, actual: {}".format(sem[-1])
            continue

        semesters.add((sem[:4], season))
    return semesters