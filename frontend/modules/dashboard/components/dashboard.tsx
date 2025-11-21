import { DossierSection } from "./dossier-section";
import { DocumentsSection } from "./documents-section";
import { TasksSection } from "./tasks-section";
import { NewsSection } from "./news-section";
import { AgendaSection } from "./agenda-section";

export function Dashboard() {
  return (
    <div className="space-y-6 p-4">
      <DossierSection />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <DocumentsSection />
        <TasksSection />
        <NewsSection />
      </div>

      <AgendaSection />
    </div>
  );
}
