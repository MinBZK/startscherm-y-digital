import { create } from "zustand";
import { DocumentItem } from "@/lib/types";

interface NotificationsState {
  latestDoc: DocumentItem | null;
  hasNew: boolean;
  setLatestDoc: (doc: DocumentItem) => void;
  markAsRead: () => void;
}

export const useNotificationsStore = create<NotificationsState>((set) => ({
  latestDoc: null,
  hasNew: true,
  setLatestDoc: (doc) => set({ latestDoc: doc, hasNew: true }),
  markAsRead: () => set({ hasNew: false }),
}));
