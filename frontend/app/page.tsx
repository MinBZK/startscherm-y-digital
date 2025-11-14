import { Dashboard } from "@/modules/dashboard/components/dashboard";
import { AuthenticatedLayout } from "@/components/authenticated-layout";

export const metadata = {
  title: "Dashboard Portal",
  description: "Government information portal dashboard",
};

export default async function DashboardHome() {
  return (
    <AuthenticatedLayout>
      <Dashboard />
    </AuthenticatedLayout>
  );
}
