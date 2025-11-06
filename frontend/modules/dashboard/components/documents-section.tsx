import { SectionCard } from "./card-section";
import { getDocumentsData } from "@/modules/dashboard/actions/documents-server-util";
import { DocumentItem } from "@/lib/types";
import { DocumentItemComponent } from "./document-item";

export async function DocumentsSection() {
  const docs = await getDocumentsData();
  return (
    <SectionCard
      title="Laatste documenten"
      buttonLabel="Alle documenten"
      buttonAction="Alle documenten"
    >
      {docs.map((doc: DocumentItem, idx: number) => (
        <DocumentItemComponent
          key={`${doc.name}-${idx}`}
          document={doc}
          bordered={idx !== docs.length - 1}
        />
      ))}
    </SectionCard>
  );
}
