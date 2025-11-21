"use client";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { MessageCircle, Phone, Video, LucideUser } from "lucide-react";
import React from "react";
import { FaLinkedin, FaInstagram } from "react-icons/fa";
import agendaDataRawUntyped from "@/dummydata/data_calendar_new.json";
import { Button } from "@/components/ui/button";

function AgendaGrid() {
  // Data ophalen
  const agendaDataRaw: any = agendaDataRawUntyped;
  const weekKey = Object.keys(agendaDataRaw)[0];
  const events = agendaDataRaw[weekKey] as any[];
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  const todayEvents = events.filter(
    (ev: any) => ev.date.slice(0, 10) === todayStr
  );

  // Tijdlijn: 8:00 tot 18:00, 11 kolommen (per uur)
  const startHour = 8;
  const endHour = 18;
  const hours = [];
  for (let h = startHour; h <= endHour; h++) {
    hours.push(h);
  }

  // Helper: tijd naar kolom-index (0 = 8:00)
  function timeToColIdx(time: string) {
    const [hour, minute] = time.split(":").map(Number);
    return hour - startHour + (minute >= 30 ? 0.5 : 0);
  }

  // Render
  return (
    <div className="border rounded-lg bg-white">
      {/* Uur labels */}
      <div className="grid grid-cols-11 border-b">
        {hours.map((h, idx) => (
          <div key={idx} className="text-xs text-gray-500 text-center py-1">
            {h}
          </div>
        ))}
      </div>
      {/* Raster en afspraken */}
      <div className="relative h-12">
        {/* Grijze blokken voor vrije tijd */}
        <div className="absolute inset-0 grid grid-cols-11 h-full">
          {hours.map((_, idx) => (
            <div
              key={idx}
              className="border-r border-gray-200 last:border-none bg-gray-50 h-full"
            />
          ))}
        </div>
        {/* Afspraken */}
        {todayEvents.map((event: any, idx: number) => {
          const start = timeToColIdx(event.start.slice(11, 16));
          const end = timeToColIdx(event.end.slice(11, 16));
          const left = `${(start / (endHour - startHour)) * 100}%`;
          const width = `${((end - start) / (endHour - startHour)) * 100}%`;
          return (
            <div
              key={idx}
              className="absolute top-1 left-0 h-8 bg-[#E6F1FA] text-[#027BC7] text-xs font-semibold rounded-md flex items-center px-2 shadow border border-[#B3D6F2]"
              style={{ left, width, minWidth: 48 }}
              title={event.title}
            >
              <span className="font-bold mr-2">
                {event.start.slice(11, 16)}
              </span>
              <span className="truncate">{event.title}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ProfileSidebar({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTitle className="sr-only">Profiel</SheetTitle>
      <SheetContent
        side="right"
        className="p-0 w-full max-w-md border-none shadow-2xl flex flex-col"
        style={{ boxShadow: "0 0 32px 0 rgba(0,0,0,0.10)" }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-6 pt-6 pb-2 border-b">
          <LucideUser fill="black" className="h-7 w-7 text-black fill-black" />
          <span className="text-xl font-bold text-black">Profiel</span>
        </div>
        {/* Profiel info grid */}
        <div className="flex gap-4 px-6 py-4 border-b items-center">
          {/* Foto met statusdot */}
          <div className="row-span-2 relative flex justify-start">
            <Avatar className="w-24 h-24">
              <AvatarImage src="/hc-image1.png" alt="Profile" />
              <AvatarFallback>MV</AvatarFallback>
            </Avatar>
            <span className="absolute bottom-2 left-19 block w-6 h-6 rounded-full border-2 border-white bg-green-500" />
          </div>
          <div>
            {/* Naam + functie */}
            <div className="flex flex-col items-start">
              <span className="text-lg font-semibold text-black">
                Marieke de Vries
              </span>
              <span className="text-gray-500 text-sm">
                Medewerker scankamer
              </span>
            </div>
            {/* Contact icons */}
            <div className="flex gap-3 mt-2">
              <Button
                className="rounded-full border-hemelblauw text-hemelblauw hover:text-hemelblauw"
                variant="outline"
                size="icon"
              >
                <MessageCircle className="h-4 w-4" />
              </Button>
              <Button
                className="rounded-full border-hemelblauw text-hemelblauw hover:text-hemelblauw"
                variant="outline"
                size="icon"
              >
                <Phone className="h-4 w-4" />
              </Button>
              <Button
                className="rounded-full border-hemelblauw text-hemelblauw hover:text-hemelblauw"
                variant="outline"
                size="icon"
              >
                <Video className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        {/* Tabs */}
        <Tabs defaultValue="contact" className="w-full flex-1 flex flex-col">
          <TabsList className="w-full flex gap-2 bg-transparent border-b border-gray-200 mb-8 px-6 pt-6">
            <TabsTrigger
              value="contact"
              className="flex-1 text-lg font-bold data-[state=active]:text-[#027BC7] border-b-2 border-transparent data-[state=active]:border-[#027BC7] data-[state=inactive]:text-gray-400 rounded-none"
            >
              Contact
            </TabsTrigger>
            <TabsTrigger
              value="about"
              className="flex-1 text-lg font-bold data-[state=active]:text-[#027BC7] border-b-2 border-transparent data-[state=active]:border-[#027BC7] data-[state=inactive]:text-gray-400 rounded-none"
            >
              Over mij
            </TabsTrigger>
            <TabsTrigger
              value="org"
              className="flex-1 text-lg font-bold data-[state=active]:text-[#027BC7] border-b-2 border-transparent data-[state=active]:border-[#027BC7] data-[state=inactive]:text-gray-400 rounded-none"
            >
              Organisatie
            </TabsTrigger>
          </TabsList>
          {/* Contact Tab */}
          <TabsContent value="contact" className="flex flex-col flex-1 px-6">
            {/* Contactgegevens */}
            <div className="mb-6 mt-2">
              <div className="text-xs text-gray-500">e-mail adres</div>
              <div className="text-base font-medium text-black mb-2">
                marieke@minvws.nl
              </div>
              <div className="text-xs text-gray-500">mobiele telefoon</div>
              <div className="text-base font-medium text-black mb-2">
                +31 6 1234 5678
              </div>
              <div className="text-xs text-gray-500">afdeling</div>
              <div className="text-base font-medium text-black mb-2">
                Informatiebeheer
              </div>
              <div className="text-xs text-gray-500">locatie</div>
              <div className="text-base font-medium text-black mb-2">
                Beatrixpark | Wilhelmina van Pruisenweg 52, 2595 AN Den Haag
              </div>
              <div className="text-xs text-gray-500">werkdagen</div>
              <div className="text-base font-medium text-black mb-2">
                Ma, di, woe, do en vri
              </div>
            </div>
            {/* Agenda */}
            <div className="mb-8">
              <div className="text-lg font-bold text-black mb-2">vandaag</div>
              <AgendaGrid />
            </div>
            {/* Prive/socials */}
            <div className="mt-auto pb-6">
              <div className="text-lg font-bold text-black mb-2">Prive</div>
              <div className="text-xs text-gray-500 mb-1">social</div>
              <div className="flex flex-col gap-1">
                <a
                  href="#"
                  className="flex items-center gap-2 hover:text-[#027BC7] text-black"
                >
                  <FaLinkedin size={18} />
                  /marieke-devries99
                </a>
                <a
                  href="#"
                  className="flex items-center gap-2 hover:text-[#027BC7] text-black"
                >
                  <FaInstagram size={18} />
                  /marieke-devr
                </a>
              </div>
            </div>
          </TabsContent>
          {/* Over mij Tab */}
          <TabsContent value="about" className="flex flex-col flex-1 px-6">
            <div className="text-gray-700 text-base mt-4">
              <span className="italic">
                Hier komt de persoonlijke informatie van de gebruiker.
              </span>
            </div>
          </TabsContent>
          {/* Organisatie Tab */}
          <TabsContent value="org" className="flex flex-col flex-1 px-6">
            <div className="text-gray-700 text-base mt-4">
              <span className="italic">
                Hier komt de organisatie-informatie van de gebruiker.
              </span>
            </div>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
