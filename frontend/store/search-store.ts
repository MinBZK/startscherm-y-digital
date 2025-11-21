import { create } from "zustand";
import { DashboardSearchFilters } from "@/lib/types";

interface SearchStoreState {
  selectedResultId: string | null;
  filters: DashboardSearchFilters;
  setSelectedResultId: (id: string | null) => void;
  setFilter: (key: string, value: string) => void;
  clearFilters: () => void;
}

export const useSearchStore = create<SearchStoreState>((set) => ({
  selectedResultId: null,
  filters: {},
  setSelectedResultId: (id) => set({ selectedResultId: id }),
  setFilter: (key, value) =>
    set((state) => {
      const newFilters = { ...state.filters };
      if (newFilters[key] === value) {
        // Same value exists, remove the filter
        delete newFilters[key];
      } else {
        // Different value or doesn't exist, set the new value
        newFilters[key] = value;
      }
      return { filters: newFilters };
    }),
  clearFilters: () => set({ filters: {} }),
}));
