import { MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DossierLink } from "./dossier-link";
import { getDossiersData } from "@/modules/dashboard/actions/dossiers-server-util";
import { DossierItem } from "@/lib/types";

export async function DossierSection() {
  const dossiers = await getDossiersData();
  return (
    <div className="bg-white p-4 rounded-lg">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-2xl font-extrabold">Dossiers</h2>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5" />
        </Button>
      </div>
      <hr />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 mt-4">
        {dossiers.map((dos: DossierItem, idx) => (
          <DossierLink dossier={dos} key={`${idx}`} />
        ))}
      </div>
    </div>
  );
}
