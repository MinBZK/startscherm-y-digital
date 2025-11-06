import { cookies } from 'next/headers';
import { Dashboard } from "@/modules/dashboard/components/dashboard";
import { Sidebar } from "@/modules/dashboard/components/dashboard-sidebar";
import { Header } from "@/app/dashboard/components/header";
import { getDossiersData } from "@/modules/dashboard/actions/dossiers-server-util";
import { verifyAccessToken } from "@/lib/auth/verify";
import { LoginGate } from "@/components/login-gate";

export const metadata = {
  title: "Dashboard Portal",
  description: "Government information portal dashboard",
};

export default async function DashboardHome() {
  const cookieStore = await cookies();
  const token = cookieStore.get?.('bsw_access')?.value;

  if (!token) {
    return <LoginGate />;
  }

  try {
    await verifyAccessToken(token);
  } catch {
    return <LoginGate />;
  }

  const dossiers = await getDossiersData();
  return (
    <main className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar dossiers={dossiers} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4">
          <Dashboard />
        </main>
      </div>
    </main>
  );
}
