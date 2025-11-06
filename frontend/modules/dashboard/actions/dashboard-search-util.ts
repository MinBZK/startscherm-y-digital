"use server";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { SearchResultsResponse, DashboardSearchFilters } from "@/lib/types";
import searchResultsData from "@/dummydata/sample_search_metadata.json";
import { buildAuthHeaders } from "./auth-headers";

interface SearchParams {
  query: string;
  filters: DashboardSearchFilters;
}

export async function getDashboardSearch({
  query,
  filters,
}: SearchParams): Promise<SearchResultsResponse> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((r) => setTimeout(r, 500));
    return searchResultsData as unknown as SearchResultsResponse;
  }
  if (!query) return { results: 0, hits: [] };
  const res = await fetch(`${API_BASE_URL}${API_ENDPOINTS.search.dashboard}`, {
    method: "POST",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ query, filters }),
  });
  if (!res.ok) {
    throw new Error("Failed to fetch search results");
  }
  return res.json();
}
