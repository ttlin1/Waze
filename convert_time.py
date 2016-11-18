from datetime import tzinfo, timedelta, datetime
from pytz import timezone

eastern = timezone('US/Eastern')

def convert_to_ordinal(milliseconds):
    return datetime.fromtimestamp(milliseconds/1000.0, eastern)


def convert_to_milliseconds(datetime_object):
    # datetime(year, month, day, hour, minute, second, microsecond)
    return (datetime_object - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000.0 + 14400000
