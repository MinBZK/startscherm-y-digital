"use server";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

import rawAgendaData from "@/dummydata/data_calendar_new.json";
import { AgendaWeek, AgendaDay, AgendaEvent } from "@/lib/types";
import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { buildAuthHeaders } from "./auth-headers";

export async function getAgendaData(): Promise<AgendaWeek[]> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return transformAgendaData(rawAgendaData);
  }

  const URL = `${API_BASE_URL}${API_ENDPOINTS.calendar.getWeekEvents}`;
  const response = await fetch(URL, {
    method: "GET",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
  });

  if (response.ok) {
    const data = await response.json();
    return transformAgendaData(data);
  } else {
    console.error("Error getting agenda data:", response.statusText);
  }

  return [];
}

function transformAgendaData(rawData: any): AgendaWeek[] {
  if (rawData.length === 0) return [];

  const weekKey = Object.keys(rawData)[0];
  const events = rawData[weekKey] as any[];
  const daysMap: Record<string, AgendaDay> = {};

  // Find the first event date to determine the week boundaries
  const firstDateStr =
    events.length > 0
      ? events[0].date.slice(0, 10)
      : new Date().toISOString().slice(0, 10);
  const firstDate = new Date(firstDateStr);
  const monday = new Date(firstDate);
  monday.setDate(firstDate.getDate() - ((firstDate.getDay() + 6) % 7));

  // Calculate the end of the week (Friday)
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);

  // Filter events to only include those within the same week (Monday-Friday)
  const weekEvents = events.filter((ev) => {
    const eventDate = new Date(ev.date);
    return eventDate >= monday && eventDate <= friday;
  });

  for (const ev of weekEvents) {
    const dateStr = ev.date.slice(0, 10);
    if (!daysMap[dateStr]) {
      daysMap[dateStr] = {
        id: dateStr,
        date: dateStr,
        dayOfWeek: ev.dayOfWeek,
        events: [],
      };
    }
    const agendaEvent: AgendaEvent = {
      title: ev.title,
      start: { dateTime: ev.start, timeZone: ev.timeZone },
      end: { dateTime: ev.end, timeZone: ev.timeZone },
      organizer: ev.organizer,
      meetingLocation: ev.meetingLocation,
      relatedToDossier: ev.relatedToDossier || null,
      link: ev.link || null,
    };
    daysMap[dateStr].events.push(agendaEvent);
  }

  // ensure whole week is present (Monday-Friday only)
  for (let i = 0; i < 5; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const iso = d.toISOString().slice(0, 10);
    if (!daysMap[iso]) {
      daysMap[iso] = {
        id: iso,
        date: iso,
        dayOfWeek: d.toLocaleDateString("en-US", { weekday: "long" }),
        events: [],
      };
    }
  }

  const week: AgendaDay[] = Object.values(daysMap).sort((a, b) =>
    a.date.localeCompare(b.date)
  );

  const agenda: AgendaWeek = { [weekKey]: week };
  return [agenda];
}
