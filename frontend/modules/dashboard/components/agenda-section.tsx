import { MoreVertical } from "lucide-react";
import { PropsWithChildren } from "react";
import { Button } from "@/components/ui/button";
import { getCurrentAgendaWeek } from "@/modules/dashboard/actions/agenda-server-util";
import { cn } from "@/lib/utils";

const FORMATTER_MONTH = new Intl.DateTimeFormat("nl-NL", {
  month: "long",
});

const FORMATTER_WEEK_DAY_LABEL = new Intl.DateTimeFormat("nl-NL", {
  weekday: "short",
});

const FORMATTER_DATE_DAY = new Intl.DateTimeFormat("nl-NL", {
  day: "numeric",
});

export async function AgendaSection() {
  const eventsPerDate = await getCurrentAgendaWeek();
  const daysOfTheWeek = getDaysOfCurrentWeek();
  const today = getDateString(new Date());

  return (
    <div className="bg-white rounded-xl shadow-sm">
      <div className="flex justify-between items-center py-6 pl-6 pr-3">
        <h2 className="text-2xl font-extrabold leading-none">
          Agenda
          <span className="text-black inline-block pl-3 ml-3 border-l border-gray-200">
            {FORMATTER_MONTH.format(new Date())}
          </span>
        </h2>

        <div className="flex gap-2">
          {/* Disable navigation, as API currently only provides current week */}
          {/* <Button variant="outline" size="icon" className="h-8 w-8 p-0">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm">
            <span className="ml-1">Vandaag</span>
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 p-0">
            <ChevronRight className="h-4 w-4" />
          </Button> */}
          <Button variant="ghost" size="icon">
            <MoreVertical size={20} />
          </Button>
        </div>
      </div>

      <div className="grid grid-rows-[auto_auto] grid-cols-5 grid-flow-col w-full">
        {daysOfTheWeek.map((day) => {
          const dateStr = getDateString(day);
          const events = eventsPerDate[dateStr]?.events || [];
          return (
            <div
              key={dateStr}
              aria-current={dateStr === today ? "date" : undefined}
              className="contents group"
              role="row"
            >
              <div className="border-r border-y group-last:border-r-0 border-gray-200 flex-1 flex items-center justify-between py-2 px-4 min-h-8">
                <span className="group-aria-current-date:text-lintblauw group-aria-current-date:font-bold text-lg text-gray-500">
                  {FORMATTER_WEEK_DAY_LABEL.format(day)}
                </span>
                <span className="flex-none font-bold flex items-center justify-center rounded-full group-aria-current-date:size-7 group-aria-current-date:bg-lintblauw group-aria-current-date:text-white">
                  {FORMATTER_DATE_DAY.format(day)}
                </span>
              </div>

              <div className="border-r group-last:border-r-0 border-gray-200 divide-y divide-gray-200 flex-1 min-w-0 flex flex-col min-h-96 px-2 gap-1 py-1 group-aria-current-date:bg-lichtblauw/10">
                {events.map(
                  ({
                    link,
                    start,
                    end,
                    title,
                    meetingLocation,
                    organizer,
                    relatedToDossier,
                  }) => (
                    <EventWrapper key={link} link={link}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-lintblauw font-semibold">
                          {start.slice(11, 16)}
                          {end ? ` - ${end.slice(11, 16)}` : ""}
                        </span>
                      </div>
                      <div className="text-base font-bold">{title}</div>
                      {relatedToDossier && (
                        <div className="text-xs text-lintblauw truncate">
                          &uarr; {relatedToDossier}
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-1">
                        {meetingLocation}
                      </div>
                      <div className="text-xs text-gray-500">{organizer}</div>
                    </EventWrapper>
                  )
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function EventWrapper({
  children,
  link,
}: PropsWithChildren<{ link: string | null }>) {
  return link ? (
    <a
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      className="bg-white flex flex-col gap-1 shadow-sm min-h-20 transition hover:ring-2 hover:ring-lichtblauw/40 focus:outline-none cursor-pointer px-3 py-4 rounded-lg"
      style={{ textDecoration: "none" }}
    >
      {children}
    </a>
  ) : (
    <div className="bg-white flex flex-col gap-1 shadow-sm min-h-20 px-3 py-4 rounded-lg">
      {children}
    </div>
  );
}

function getDaysOfCurrentWeek(): Date[] {
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0 (Sun) to 6 (Sat)
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Adjust if Sunday

  const monday = new Date(today);
  monday.setDate(today.getDate() + mondayOffset);

  const weekDays: Date[] = [];
  for (let i = 0; i < 5; i++) {
    const day = new Date(monday);
    day.setDate(monday.getDate() + i);
    weekDays.push(day);
  }
  return weekDays;
}

function getDateString(date: Date): string {
  return date.toISOString().slice(0, 10);
}
