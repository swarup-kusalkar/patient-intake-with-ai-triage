from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
CLINIC_TZ = ZoneInfo("Asia/Kolkata")

def parse_date_param(date_str: str) -> date:
    if date_str.strip().lower() == "today":
        return datetime.now(tz=timezone.utc).date()
    return date.fromisoformat(date_str.strip())


def day_range(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min, tzinfo=CLINIC_TZ)
    end = start + timedelta(days=1)
    return start, end