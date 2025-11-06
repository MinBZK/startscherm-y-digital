import { MoreVertical, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getAgendaData } from "@/modules/dashboard/actions/agenda-server-util";
import { AgendaDay } from "@/lib/types";

const TODAY = "Tuesday";

export async function AgendaSection() {
  const agendaData = await getAgendaData();

  // Neem de eerste week als array van dagen (zonder genest object)
  const week: AgendaDay[] =
    agendaData[0]?.[Object.keys(agendaData[0])[0]] ?? [];

  const renderDayHeader = (day: AgendaDay, idx: number) => {
    const isToday = day.dayOfWeek === TODAY;
    return (
      <div
        key={day.id}
        className={
          `flex-1 basis-0 min-w-0 flex items-center justify-between px-2 py-2 min-h-[32px] ` +
          (idx !== week.length - 1 ? "border-r border-gray-200" : "")
        }
      >
        <span
          className={
            isToday
              ? "text-lintblauw font-bold text-lg"
              : "text-gray-500 text-lg"
          }
        >
          {day.dayOfWeek}
        </span>
        <span
          className={
            isToday
              ? "flex items-center justify-center w-7 h-7 rounded-full bg-lintblauw text-white text-base font-bold"
              : "text-black font-bold text-base"
          }
        >
          {parseInt(day.date.split("-")[2], 10)}
        </span>
      </div>
    );
  };

  const renderEventCard = (event: AgendaDay["events"][number], key: number) => {
    const content = (
      <>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-lintblauw font-semibold">
            {event.start.dateTime.slice(11, 16)}
            {event.end ? ` - ${event.end.dateTime.slice(11, 16)}` : ""}
          </span>
        </div>
        <div className="text-base font-bold">{event.title}</div>
        {event.relatedToDossier && (
          <div className="text-xs text-lintblauw truncate">
            &uarr; {event.relatedToDossier}
          </div>
        )}
        <div className="text-xs text-gray-500 mt-1">
          {event.meetingLocation}
        </div>
        <div className="text-xs text-gray-500">{event.organizer}</div>
      </>
    );

    if (event.link) {
      return (
        <a
          key={key}
          href={event.link}
          target="_blank"
          rel="noopener noreferrer"
          className="border-b border-gray-200 last:border-b-0 bg-white flex flex-col gap-1 shadow-sm min-h-[80px] transition hover:ring-2 hover:ring-lichtblauw/40 focus:outline-none cursor-pointer px-3 py-4 rounded-lg"
          style={{ textDecoration: "none" }}
        >
          {content}
        </a>
      );
    }

    return (
      <div
        key={key}
        className="border-b border-gray-200 last:border-b-0 bg-white flex flex-col gap-1 shadow-sm min-h-[80px] px-3 py-4 rounded-lg"
      >
        {content}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl p-8 shadow-sm">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-2xl font-extrabold text-black">Agenda</h2>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5" />
        </Button>
      </div>
      <h3 className="text-2xl font-bold mb-6 ">Mei</h3>

      <div className="flex w-full border-b border-gray-200">
        {week.map(renderDayHeader)}
      </div>

      <div className="flex w-full">
        {week.map((day, idx) => {
          const isToday = day.dayOfWeek === TODAY;
          return (
            <div
              key={day.id}
              className={
                `flex-1 basis-0 min-w-0 flex flex-col min-h-[420px] px-2 gap-1 pt-1 ` +
                (idx !== week.length - 1 ? "border-r border-gray-200" : "") +
                (isToday ? " bg-lichtblauw/10 rounded-b-2xl" : "")
              }
            >
              {day.events.map((event, idx2) => renderEventCard(event, idx2))}
            </div>
          );
        })}
      </div>

      <div className="flex justify-end mt-6 gap-2">
        <Button variant="outline" size="icon" className="h-8 w-8 p-0">
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="sm">
          <span className="ml-1">Vandaag</span>
        </Button>
        <Button variant="outline" size="icon" className="h-8 w-8 p-0">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
