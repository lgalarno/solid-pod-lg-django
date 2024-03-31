from datetime import datetime

import pytz


def is_session_active(ts):
    now = datetime.now(pytz.UTC).timestamp()
    return ts > now
