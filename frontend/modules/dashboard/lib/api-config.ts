export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export const API_ENDPOINTS = {
  search: {
    dashboard: "/api/search",
    assistent: "/api/pipeline",
  },
  calendar: {
    getWeekEvents: "/api/calendar/get_week_events",
  },
  documents: {
    latest: "/api/documents/latest",
    updateDocumentStatus: "/api/documents/:document_id/processed",
  },
  dossiers: {
    create: "/api/dossiers/create",
    getDossier: "/api/dossiers/dossier/:dossier_id",
    updateDossierStatus: "/api/dossiers/dossier/:dossier_id/opened",
    getLatest: "/api/dossiers/get_latest",
    getAll: "/api/dossiers/get_all",
  },
  tasks: {
    getTasks: "/api/tasks/get_tasks",
  },
  llm: {
    query: "/chat-llm",
  },
} as const;

export type ApiEndpoint = typeof API_ENDPOINTS;
