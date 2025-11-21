"use server";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

import rawAgendaData from "@/dummydata/data_calendar_new.json";
import { AgendaWeek, AgendaEvent } from "@/lib/types";
import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { buildAuthHeaders } from "./auth-headers";

export async function getCurrentAgendaWeek(): Promise<AgendaWeek> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return groupByDate(rawAgendaData);
  }

  const URL = `${API_BASE_URL}${API_ENDPOINTS.calendar.getWeekEvents}`;
  const response = await fetch(URL, {
    method: "GET",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
  });

  if (response.ok) {
    const data = await response.json();
    return groupByDate(data);
  } else {
    console.error("Error getting agenda data:", response.statusText);
  }

  return {};
}

function groupByDate(obj: Record<string, AgendaEvent[]>): AgendaWeek {
  if (!obj) {
    return {};
  }

  // get events array from the single key
  const events = obj[Object.keys(obj)[0]];
  if (!events) {
    return {};
  }

  const eventsPerDate: AgendaWeek = {};
  events.forEach((ev) => {
    const dateStr = ev.date.slice(0, 10);

    if (!eventsPerDate[dateStr]) {
      eventsPerDate[dateStr] = {
        date: dateStr,
        events: [],
      };
    }

    eventsPerDate[dateStr].events.push(ev);
  });
  return eventsPerDate;
}
