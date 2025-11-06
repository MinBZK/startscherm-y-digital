"use server";

import mockData from "@/dummydata/data3.json";
import { LegalData } from "@/lib/types";
import { API_BASE_URL, API_ENDPOINTS } from "../../dashboard/lib/api-config";

// This is a server action that returns mock data from temp.json
export async function getMockResponse(
  query: string,
  dossierId: string,
): Promise<LegalData> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 4000));
    return mockData as LegalData;
  }
  const URL = `${API_BASE_URL}${API_ENDPOINTS.search.assistent}`;

  const response = await fetch(URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: "1",
      message: query,
      dossier: dossierId ? { dossier_id: dossierId } : undefined,
    }),
  });

  if (response.ok) {
    const data = await response.json();
    return data as LegalData;
  } else {
    console.error("Error response:", response.statusText);
  }
  return mockData as LegalData;
}
