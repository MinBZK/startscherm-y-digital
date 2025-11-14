import { cookies } from "next/headers";
import { Header } from "@/app/dashboard/components/header";
import { LoginGate } from "@/components/login-gate";
import { getDossiersData } from "@/modules/dashboard/actions/dossiers-server-util";
import { Sidebar } from "@/modules/dashboard/components/dashboard-sidebar";
import { verifyAccessToken } from "@/lib/auth/verify";

interface AuthenticatedLayoutProps {
  children: React.ReactNode;
}

export async function AuthenticatedLayout({
  children,
}: AuthenticatedLayoutProps) {
  const cookieStore = await cookies();
  const token = cookieStore.get?.("bsw_access")?.value;

  if (!token) {
    console.info("[auth] No access token found - redirecting to login");
    return <LoginGate />;
  }

  try {
    await verifyTokenWithRetry(token);
  } catch (error) {
    console.error(
      "[auth] Token verification failed after all retries - redirecting to login:",
      error
    );
    return <LoginGate />;
  }

  const dossiers = await getDossiersData();

  return (
    <main className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar dossiers={dossiers} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto flex flex-col">{children}</main>
      </div>
    </main>
  );
}

export async function verifyTokenWithRetry(
  token: string,
  maxRetries = 3
): Promise<void> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await verifyAccessToken(token);
      return; // Success, exit the function
    } catch (error) {
      console.warn(
        `[auth] Token verification attempt ${attempt}/${maxRetries} failed:`,
        error
      );

      if (attempt === maxRetries) {
        console.error(
          "[auth] All token verification attempts failed - authentication required"
        );
        throw error; // Re-throw the error to trigger LoginGate
      }

      // Exponential backoff: wait 100ms, then 200ms, then 400ms
      const delay = 100 * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
}
