import { ThumbsUp, MessageSquare, Heart, Lightbulb } from "lucide-react";
import { SectionCard } from "@/modules/dashboard/components/card-section";
import React from "react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

export function NewsSection() {
  // Hardcoded nieuwsitems
  const news = [
    {
      img: "/hc-image1.png",
      title: "NIEUWS RvIHH",
      time: "Vandaag 9:34",
      description:
        "Nog 10 plaatsen voor post-hbo Archivistiek. Pak je kans en meld je nu aan!",
      likes: 34,
      hearts: 9,
      comments: 2,
      bulbs: 3,
    },
    {
      img: "/hc-image2.png",
      title: "NIEUWS Rijksbreed",
      time: "Vandaag 9:34",
      description: "Nieuwe standpunt inzet generatieve AI",
      likes: 12,
      hearts: 18,
      comments: 18,
      bulbs: 0,
    },
  ];

  // Util functie voor reactie-iconen (exclusief comments)
  function getReactionIcons(item: {
    likes: number;
    hearts: number;
    bulbs: number;
  }) {
    const icons: {
      icon: React.ReactNode;
      count: number;
      color: string;
      label: string;
    }[] = [];
    if (item.likes > 0)
      icons.push({
        icon: <ThumbsUp className="h-4 w-4" />,
        count: item.likes,
        color: "text-black",
        label: "Like",
      });
    if (item.hearts > 0)
      icons.push({
        icon: <Heart className="h-4 w-4" fill="red" />,
        count: item.hearts,
        color: "text-red-600",
        label: "Heart",
      });
    if (item.bulbs > 0)
      icons.push({
        icon: <Lightbulb className="h-4 w-4" stroke="#FACC15" />,
        count: item.bulbs,
        color: "text-yellow-500",
        label: "Interesting",
      });
    return icons;
  }

  return (
    <SectionCard
      title="Laatste nieuws"
      buttonLabel="Meer nieuws"
      buttonAction="Meer nieuws"
    >
      {news.map((item, idx) => {
        const icons = getReactionIcons(item);
        const total = icons.reduce((sum, i) => sum + i.count, 0);
        return (
          <div
            key={item.title}
            className={`flex gap-3 px-6 py-4 min-h-[112px] ${
              idx !== news.length - 1 ? "border-b border-gray-200" : ""
            }`}
          >
            <div className="flex-shrink-0 w-20 h-20 bg-gray-200 rounded overflow-hidden">
              <img
                src={item.img}
                alt="News thumbnail"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-xs font-bold !text-roze">{item.title}</h3>
                <span className="text-xs font-bold text-gray-700">
                  {item.time}
                </span>
              </div>
              <p className="font-bold text-base text-black leading-tight mb-2">
                {item.description}
              </p>
              <div className="flex items-center gap-4 mt-2 relative">
                {/* Reactie-iconen met dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      className="flex items-center gap-1 bg-gray-50 rounded-full px-2 py-1 cursor-pointer border border-gray-200 hover:bg-gray-100 transition"
                      type="button"
                    >
                      {icons.map((i, iconIdx) => (
                        <span
                          key={iconIdx}
                          className={`flex items-center ${i.color}`}
                        >
                          {i.icon}
                        </span>
                      ))}
                      <span className="ml-2 text-xs font-semibold text-gray-700">
                        {total}
                      </span>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    {icons.map((i, iconIdx) => (
                      <DropdownMenuItem
                        key={iconIdx}
                        className="flex items-center gap-2"
                      >
                        <span className={i.color}>{i.icon}</span>
                        <span className="text-xs text-gray-700">{i.label}</span>
                        <span className="ml-auto text-xs font-bold">
                          {i.count}
                        </span>
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                {/* Comments los */}
                <div className="flex items-center gap-1 text-xs text-[#027BC7] ml-4">
                  <MessageSquare className="h-4 w-4" />
                  <span>{item.comments}</span>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </SectionCard>
  );
}
