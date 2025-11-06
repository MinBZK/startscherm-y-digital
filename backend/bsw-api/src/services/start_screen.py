from services import documents, tasks, calendar, news, messages


async def get_start_screen_data(user_id: str):
    # Optionally run in parallel using asyncio.gather
    latest_docs = await documents.get_latest_documents(user_id)
    pending_tasks = await tasks.get_tasks(user_id)
    calendar_events = await calendar.get_upcoming_events(user_id)
    latest_news = await news.get_news(user_id)
    user_messages = await messages.get_messages(user_id)

    return {
        "documents": latest_docs,
        "tasks": pending_tasks,
        "calendar": calendar_events,
        "news": latest_news,
        "messages": user_messages,
    }
