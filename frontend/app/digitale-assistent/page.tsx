import { AuthenticatedLayout } from "@/components/authenticated-layout";
import { LLMChat } from "@/modules/dashboard/components/llm-chat";

export const metadata = {
  title: "Digitale Assistent - Dashboard Portal",
  description: "AI-powered digital assistant for government workflows",
};

export default async function DigitaleAssistentPage() {
  return (
    <AuthenticatedLayout>
      <LLMChat />
    </AuthenticatedLayout>
  );
}
