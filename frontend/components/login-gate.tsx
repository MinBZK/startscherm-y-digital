'use client';
import { useKeycloak } from '@/components/keycloak-provider';

export function LoginGate() {
  const { isLoading, login } = useKeycloak();

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading authentication...</div>;
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Please log in</h1>
        <button
          onClick={login}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Login with Keycloak
        </button>
      </div>
    </div>
  );
}
