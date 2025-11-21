"use client";

import { useState } from "react";
import { FileText } from "lucide-react";
import { DocumentItem } from "@/lib/types";
import { DocumentProcessingPopover } from "./document-processing-popover";
import { updateDocumentStatus } from "../actions/documents-server-util";
import { transformToNextcloudUrl } from "@/lib/nextcloud-utils";

interface DocumentItemProps {
  document: DocumentItem;
  bordered?: boolean;
}

export function DocumentItemComponent({
  document,
  bordered,
}: DocumentItemProps) {
  const [showMagicWand, setShowMagicWand] = useState(
    document.show_magic_wand || false
  );

  const handleClick = async () => {
    if (document.id) {
      try {
        await updateDocumentStatus(document.id);
      } catch (e) {
        console.error("Failed to update document status", e);
      }
    }
  };

  const nextcloudUrl = transformToNextcloudUrl(
    document.url,
    document.nextcloud_id
  );

  // Toon magic wand button alleen voor transcript documenten
  const shouldShowMagicWand = document.is_transcript && showMagicWand;

  return (
    <div className="relative group">
      <div
        className={`flex items-start gap-3 px-6 py-4 min-h-[72px] ${
          bordered ? "border-b border-gray-200" : ""
        }`}
      >
        <div className="flex-shrink-0 pt-1">
          <FileText className="h-5 w-5 text-lintblauw" />
        </div>
        <div className="flex-1 min-w-0">
          <a
            href={nextcloudUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-base text-black leading-tight underline"
          >
            {document.name}
          </a>
          <p className="text-xs text-gray-500 mb-0.5">{document.filetype}</p>
          {document.linked_dossier && (
            <p className="text-xs text-lintblauw truncate leading-tight">
              &uarr; {document.linked_dossier}
            </p>
          )}
        </div>
      </div>

      {/* {shouldShowMagicWand && (
        <div className="absolute top-1/2 -translate-y-1/2 right-2 z-10">
          <DocumentProcessingPopover
            document={document}
            onClose={() => {
              setShowMagicWand(false);
              handleClick();
            }}
          />
        </div>
      )} */}
    </div>
  );
}
