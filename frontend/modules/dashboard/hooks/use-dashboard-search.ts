import { useQuery } from "@tanstack/react-query";
import { SearchResultsResponse, DashboardSearchFilters } from "@/lib/types";
import { getDashboardSearch } from "../actions/dashboard-search-util";

export function useDashboardSearch(
  query: string,
  filters: DashboardSearchFilters,
  enabled = true
) {
  return useQuery<SearchResultsResponse>({
    queryKey: ["dashboard-search", query, filters],
    queryFn: () => getDashboardSearch({ query, filters }),
    enabled,
  });
}
