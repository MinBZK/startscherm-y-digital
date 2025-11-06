"use server";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

import documentsData from "@/dummydata/data_last_docs.json";
import { DocumentItem } from "@/lib/types";
import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { buildAuthHeaders } from "./auth-headers";

export async function getDocumentsData(): Promise<DocumentItem[]> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return documentsData as DocumentItem[];
  }

  const URL = `${API_BASE_URL}${API_ENDPOINTS.documents.latest}`;

  const response = await fetch(URL, {
    method: "GET",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
    cache: "no-store",
  });

  if (response.ok) {
    const data = await response.json();
    return data as DocumentItem[];
  } else {
    console.error("Error getting documents data:", response.statusText);
  }

  return [];
}

export async function updateDocumentStatus(document_id: string) {
  const URL = `${API_BASE_URL}${API_ENDPOINTS.documents.updateDocumentStatus?.replace(
    ":document_id",
    document_id
  )}`;

  const response = await fetch(URL, {
    method: "PATCH",
    headers: await buildAuthHeaders(),
  });

  if (response.ok) {
    return true;
  } else {
    console.error("Error updating document status:", response.statusText);
    return false;
  }
}
