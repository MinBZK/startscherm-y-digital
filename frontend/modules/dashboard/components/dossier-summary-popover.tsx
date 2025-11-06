"use client";

import { useState } from "react";
import { Wand2, Plus, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { DossierItem, DossierSummary } from "@/lib/types";

interface DossierSummaryPopoverProps {
  dossier: DossierItem;
  onClose: () => void;
}

export function DossierSummaryPopover({
  dossier,
  onClose,
}: DossierSummaryPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [summary, setSummary] = useState<DossierSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleOpen = async () => {
    setIsOpen(true);
    setIsLoading(true);

    try {
      // TODO: Implementeer echte API call naar backend
      // Voor nu gebruiken we mock data
      const mockSummary: DossierSummary = {
        dossier_id: dossier.dossier_id,
        summary:
          "Dit dossier betreft een klacht over Piet de Vries. De klacht is ingediend op basis van vermeende schending van privacyregelgeving. Het document bevat gedetailleerde informatie over de incidenten en de impact op de betrokken partijen.",
        nextStep:
          "Plan een intakegesprek met de klager om de details van de klacht te bespreken en eventuele aanvullende documentatie te verzamelen.",
        followUpQuestions: [
          "Wie zijn de experts van dit onderwerp?",
          "Komt deze situatie vaker voor?",
        ],
      };

      // Simuleer API delay
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setSummary(mockSummary);
    } catch (error) {
      console.error("Failed to fetch dossier summary:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    onClose();
  };

  return (
    <Popover
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          handleClose();
        }
        setIsOpen(open);
      }}
    >
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="w-8 h-8 rounded-full bg-white border-hemelblauw text-lintblauw hover:bg-sky-50 hover:border-lintblauw shadow-md transition-all duration-200 hover:scale-105"
          onClick={handleOpen}
        >
          <Wand2 className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-0" align="end" sideOffset={8}>
        <Card className="border-0 shadow-none">
          <CardHeader className=" text-lintblauw rounded-t-lg">
            <div className="flex items-center gap-2">
              <Wand2 className="h-5 w-5" />
              <h3 className="font-semibold">Het dossier in het kort</h3>
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
              </div>
            ) : summary ? (
              <div className="space-y-4">
                {/* Summary Section */}
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <FileText className="h-5 w-5 text-sky-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">
                        Klaagschrift over Piet de Vries
                      </h4>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {summary.summary}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Next Step Section */}
                <div className="pt-3 border-t border-gray-200">
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {summary.nextStep}
                  </p>
                </div>

                {/* Follow-up Questions */}
                <div className="pt-3 border-t border-gray-200">
                  <div className="space-y-2">
                    {summary.followUpQuestions.map((question, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <Plus className="h-4 w-4 text-sky-600 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">
                          {question}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Er is een fout opgetreden bij het laden van de samenvatting.
              </div>
            )}
          </CardContent>
        </Card>
      </PopoverContent>
    </Popover>
  );
}
