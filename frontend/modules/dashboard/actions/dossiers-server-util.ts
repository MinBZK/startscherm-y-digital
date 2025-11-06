"use server";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

import dossiersData from "@/dummydata/data_last_dossiers.json";
import { DossierItem } from "@/lib/types";
import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { buildAuthHeaders } from "./auth-headers";

export async function getDossiersData(): Promise<DossierItem[]> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return dossiersData as DossierItem[];
  }

  const URL = `${API_BASE_URL}${API_ENDPOINTS.dossiers.getLatest}`;

  const response = await fetch(URL, {
    method: "GET",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
  });

  if (response.ok) {
    const data = await response.json();
    return data as DossierItem[];
  } else {
    console.error("Error getting dossiers data:", response.statusText);
  }

  return [];
}

export async function updateDossierStatus(dossier_id: string) {
  const URL = `${API_BASE_URL}${API_ENDPOINTS.dossiers.updateDossierStatus.replace(
    ":dossier_id",
    dossier_id
  )}`;

  const response = await fetch(URL, {
    method: "PATCH",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
  });

  if (response.ok) {
    return true;
  } else {
    console.error("Error updating dossier status:", response.statusText);
    return false;
  }
}
