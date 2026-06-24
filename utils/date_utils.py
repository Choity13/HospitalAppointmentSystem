from datetime import datetime, date, time
import pytz

tz = pytz.timezone('Asia/Dhaka')


def make_tz_aware(dt):
    """Make a datetime timezone-aware if it's not already."""
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return tz.localize(dt, is_dst=None)
    return dt


def get_current_time():
    """Get current Asia/Dhaka timezone-aware datetime."""
    return datetime.now(tz)


def get_current_date():
    """Get current Asia/Dhaka date."""
    return get_current_time().date()
