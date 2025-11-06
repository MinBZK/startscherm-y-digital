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
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
  clearFilters: () => set({ filters: {} }),
}));
