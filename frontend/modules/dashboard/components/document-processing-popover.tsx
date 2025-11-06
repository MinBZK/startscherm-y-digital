"use client";

import { useState } from "react";
import { Wand2, FileText, FileCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { DocumentItem, DocumentProcessingResponse } from "@/lib/types";

interface DocumentProcessingPopoverProps {
  document: DocumentItem;
  onClose: () => void;
}

export function DocumentProcessingPopover({
  document,
  onClose,
}: DocumentProcessingPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [processingType, setProcessingType] = useState<string | null>(null);

  const handleOpen = async () => {
    setIsOpen(true);
  };

  const handleClose = () => {
    setIsOpen(false);
    onClose();
  };

  const handleProcessDocument = async (type: "closure_letter" | "summary") => {
    setIsLoading(true);
    setProcessingType(type);

    try {
      // TODO: Implementeer echte API call naar backend
      // Voor nu gebruiken we mock data
      const mockResponse: DocumentProcessingResponse = {
        success: true,
        data: {
          closure_letter_url:
            type === "closure_letter"
              ? `https://ydigital.sharepoint.com/sites/ProefopstelingBSW/_layouts/15/Doc.aspx?sourcedoc=%7B3DED7FC5-C1C2-48AC-A08E-4F80C917AEF3%7D&file=Afdoeningsbrief%20-%20${document.name.replace(
                  ".docx",
                  ""
                )}.docx&action=default&mobileredirect=true`
              : undefined,
          summary_url:
            type === "summary"
              ? `https://ydigital.sharepoint.com/sites/ProefopstelingBSW/_layouts/15/Doc.aspx?sourcedoc=%7B3DED7FC5-C1C2-48AC-A08E-4F80C917AEF3%7D&file=Samenvatting%20${document.name.replace(
                  ".docx",
                  ""
                )}.docx&action=default&mobileredirect=true`
              : undefined,
        },
      };

      // Simuleer API delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Open the generated document in a new tab
      const url =
        type === "closure_letter"
          ? mockResponse.data?.closure_letter_url
          : mockResponse.data?.summary_url;

      if (url) {
        window.open(url, "_blank", "noopener,noreferrer");
      }

      // Close the popover
      handleClose();
    } catch (error) {
      console.error("Failed to process document:", error);
    } finally {
      setIsLoading(false);
      setProcessingType(null);
    }
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
      <PopoverContent className="w-[420px] p-0" align="end" sideOffset={8}>
        <Card className="border-0 shadow-none">
          <CardHeader className="text-lintblauw rounded-t-lg">
            <div className="flex items-center gap-2">
              <Wand2 className="h-5 w-5" />
              <h3 className="font-semibold">Document verwerken</h3>
            </div>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">
                    {processingType === "closure_letter"
                      ? "Afdoeningsbrief wordt gegenereerd..."
                      : "Samenvatting wordt gegenereerd..."}
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-gray-600 mb-4">
                  Kies een optie om de transcriptie te verwerken:
                </p>

                {/* Option 1: Generate Closure Letter */}
                <Button
                  variant="outline"
                  className="w-full justify-start h-auto p-4 text-left whitespace-normal"
                  onClick={() => handleProcessDocument("closure_letter")}
                >
                  <div className="flex items-start gap-3">
                    <FileCheck className="h-5 w-5 text-sky-600 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <h4 className="font-medium text-gray-900 mb-1">
                        Genereer afdoeningsbrief
                      </h4>
                      <p className="text-sm text-gray-600 leading-relaxed break-words">
                        Maak gebruik van de context van het dossier en de
                        aspecten die zijn besproken in de hoorzitting
                      </p>
                    </div>
                  </div>
                </Button>

                {/* Option 2: Generate Summary */}
                <Button
                  variant="outline"
                  className="w-full justify-start h-auto p-4 text-left whitespace-normal"
                  onClick={() => handleProcessDocument("summary")}
                >
                  <div className="flex items-start gap-3">
                    <FileText className="h-5 w-5 text-sky-600 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <h4 className="font-medium text-gray-900 mb-1">
                        Genereer samenvatting
                      </h4>
                      <p className="text-sm text-gray-600 leading-relaxed break-words">
                        Maak een samenvatting op basis van de transcriptie van
                        de hoorzitting
                      </p>
                    </div>
                  </div>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </PopoverContent>
    </Popover>
  );
}
