import { ReactNode } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface DossierCardProps {
  badge: ReactNode;
  title: string;
  subtitle: string;
  progress?: number;
}

export function DossierCard({
  badge,
  title,
  subtitle,
  progress,
}: DossierCardProps) {
  return (
    <Card className="w-full h-full flex flex-col min-h-[120px]">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">{badge}</div>
      </CardHeader>
      <CardContent className="flex flex-col flex-grow justify-between gap-2">
        <div>
          <h3 className="font-medium mb-2 text-sm sm:text-base leading-tight line-clamp-2">
            {title}
          </h3>
          <div className="text-xs text-gray-500 mb-2">
            <span className="line-clamp-2">{subtitle}</span>
          </div>
        </div>
        {typeof progress === "number" && (
          <div className="flex items-center gap-2 mt-2">
            <Progress value={progress} className="h-1.5 flex-grow min-w-0" />
            <div className="text-xs whitespace-nowrap flex-shrink-0">
              {progress}%
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
