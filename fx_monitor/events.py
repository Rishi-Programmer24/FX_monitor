from datetime import datetime


CENTRAL_BANK_EVENTS = [
    {
        "date": "2021-12-16",
        "label": "BoE starts hiking cycle",
        "bank": "BoE",
        "color": "#1f77b4",
    },
    {
        "date": "2022-09-22",
        "label": "BoE 50bp hike",
        "bank": "BoE",
        "color": "#1f77b4",
    },
    {
        "date": "2022-12-20",
        "label": "BoJ widens YCC band",
        "bank": "BoJ",
        "color": "#d62728",
    },
    {
        "date": "2023-07-28",
        "label": "BoJ YCC adjustment",
        "bank": "BoJ",
        "color": "#d62728",
    },
    {
        "date": "2023-09-21",
        "label": "BoE pauses at 5.25%",
        "bank": "BoE",
        "color": "#1f77b4",
    },
    {
        "date": "2024-03-19",
        "label": "BoJ exits negative rates",
        "bank": "BoJ",
        "color": "#d62728",
    },
    {
        "date": "2024-08-01",
        "label": "BoE first cut of cycle",
        "bank": "BoE",
        "color": "#1f77b4",
    },
]


def get_events_in_range(start_date: str, end_date: str):
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()

    return [
        event
        for event in CENTRAL_BANK_EVENTS
        if start <= datetime.fromisoformat(event["date"]).date() <= end
    ]
