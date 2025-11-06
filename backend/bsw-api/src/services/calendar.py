from elastic.elastic import ES
from utils.logging.logger import logger
from datetime import datetime, timedelta, time, timezone
from collections import defaultdict


async def get_all_events() -> list[dict]:
    pass


def fetch_all_events_with_scroll(es, index_name, query, scroll="2m", batch_size=1000):
    all_events = []
    response = es.search(index=index_name, body=query, scroll=scroll, size=batch_size)
    scroll_id = response["_scroll_id"]
    hits = response["hits"]["hits"]

    while hits:
        all_events.extend(hit["_source"] for hit in hits)
        response = es.scroll(scroll_id=scroll_id, scroll=scroll)
        scroll_id = response["_scroll_id"]
        hits = response["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)

    return all_events


async def get_week_events(user_id: str) -> dict:
    es = ES
    index_name = f"calendar_{user_id}"
    if not es.indices.exists(index=index_name):
        logger.warning(f"Calendar for user {user_id} does not exist. Returning empty list.")
        return []
    monday, friday = get_iso_datetime_range_this_week()
    logger.debug(f"Getting events for user {user_id} from {monday} to {friday}")
    query = {
        "query": {
            "range": {
                "start_time": {
                    "gte": monday,
                    "lt": friday
                }
            }
        }
    }

    events = fetch_all_events_with_scroll(es, index_name, query)

    sorted_events = sorted(events, key=lambda x: datetime.fromisoformat(x["start_time"]))
    
    week_number = datetime.today().isocalendar().week
    week_dict = [{"week_number": week_number, "events": sorted_events}]
    response_json = create_response_json_calendar(week_dict)

    return response_json

def create_response_json_calendar(week_list: list) -> dict:
    response = defaultdict(dict)
    
    for week in week_list:
        week_number = f"week_{week["week_number"]}"
        week_events = [
            {
                "id": i,
                "date": event["start_time"], 
                "dayOfWeek": get_day_from_iso(event["start_time"]), 
                "title": event["title"], 
                "start": event["start_time"], 
                "end": event["end_time"], 
                "timeZone": event["timezone"], 
                "organizer": event.get("organizer", ""), 
                "meetingLocation": event.get("location", ""),
                "relatedToDossier": "", 
                "link": event.get("url", "")
                }
            for i, event in enumerate(week["events"])]
        response[week_number] = week_events

    return response


def get_iso_datetime_range_this_week():
    today = datetime.now(timezone.utc)
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=5)  # Friday

    start_dt = datetime.combine(start_of_week.date(), time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_of_week.date(), time.min, tzinfo=timezone.utc)

    return start_dt.isoformat(), end_dt.isoformat()


def get_day_from_iso(iso_date: str) -> str:
    """
    Returns the day of the week (e.g., Monday) from an ISO formatted date string.
    """
    date_obj = datetime.fromisoformat(iso_date)
    return date_obj.strftime('%A')

async def open_calendar_link(calendar_id: str):
    pass