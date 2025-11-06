"use client";

import { useState } from "react";
import { DossierItem } from "@/lib/types";
import { DossierCard } from "./dossier-card";
import { DossierSummaryPopover } from "./dossier-summary-popover";
import Link from "next/link";
import { updateDossierStatus } from "../actions/dossiers-server-util";
import { transformToNextcloudUrl } from "@/lib/nextcloud-utils";

interface Props {
  dossier: DossierItem;
}

export function DossierLink({ dossier }: Props) {
  const [showMagicWand, setShowMagicWand] = useState(true);

  const handleClick = async () => {
    if (dossier.dossier_id) {
      try {
        await updateDossierStatus(dossier.dossier_id);
      } catch (e) {
        console.error("Failed to update dossier status", e);
      }
    }
  };

  // Transform the webURL to proper Nextcloud format
  const nextcloudUrl = transformToNextcloudUrl(
    dossier.url,
    dossier.file_id,
  );

  // Debug logging for development
  if (process.env.NODE_ENV === 'development') {
    console.log(`Dossier ${dossier.name}: file_id=${dossier.file_id}, url=${dossier.url}, nextcloudUrl=${nextcloudUrl}`);
  }

  // Toon magic wand button alleen voor nieuwe dossiers (is_unopened = true)
  const shouldShowMagicWand = dossier.is_unopened && showMagicWand;

  const badge = dossier.is_unopened ? (
    <span className="bg-green-500 hover:bg-green-600 text-white text-xs px-2 py-0.5 rounded">
      Nieuw verzoek
    </span>
  ) : (
    <span className="text-xs text-gray-500">
      Laatste wijziging:{" "}
      {new Date(dossier.last_modified).toLocaleString("nl-NL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })}
    </span>
  );

  return (
    <div className="relative group">
      <Link href={nextcloudUrl} onClick={handleClick}>
        <DossierCard
          badge={badge}
          title={dossier.name}
          subtitle={`Ontvangen ${new Date(dossier.date_received).toLocaleString(
            "nl-NL",
            {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            }
          )}`}
          progress={dossier.progress}
        />
      </Link>

      {shouldShowMagicWand && (
        <div className="absolute -top-2 -right-2 z-10">
          <DossierSummaryPopover
            dossier={dossier}
            onClose={() => setShowMagicWand(false)}
          />
        </div>
      )}
    </div>
  );
}
