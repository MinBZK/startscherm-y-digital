"use client";
import Image from "next/image";
import { SourcesSidebar } from "@/components/sources-sidebar";
import { useSidebarStore } from "@/store/sidebar-store";
import { cn } from "@/lib/utils";
import { schema } from "@/lib/schemes";
import { Message } from "@/lib/types";
import { MainContent } from "@/modules/assistent/components/main-content";
import { Disclaimer } from "@/components/disclaimer";
import { ChatInput } from "@/modules/assistent/components/chat-input";
import { getMockResponse } from "@/modules/assistent/actions/server-util";
import { Button } from "@/components/ui/button";
import { Menu, SquarePen } from "lucide-react";

export function AssistentDialogContent() {
  const {
    openSidebar,
    isOpen,
    setLegalData,
    setAllSources,
    closeSidebar,
    clearLegalData,
    openChat,
    closeChat,
    isChatOpen,
    setText,
    text,
    setValidationText,
    validationText,
    setDossierId,
    dossierId,
    setMessages,
    messages,
  } = useSidebarStore();

  // Track if we're at the initial state or in a chat

  const handleNewChat = () => {
    closeChat();
    setMessages([]);
    setText("");
    setValidationText("");
    setDossierId("");
    clearLegalData();
    closeSidebar();
  };

  const handleKeyDown = async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter") {
      e.preventDefault(); // Prevents default newline insertion

      const result = schema.safeParse({ text });
      if (!result.success) {
        setValidationText(
          result.error.issues[0]?.message ||
            "Er is een validatiefout opgetreden"
        );
        return;
      }
      if (!dossierId) {
        setValidationText("Kies een dossier");
        return;
      }

      const newMessage: Message = { role: "user", content: text };
      setMessages([...messages, newMessage]);
      openChat();
      openSidebar();

      const mockResponse = await getMockResponse(text, dossierId);
      if (result.success) {
        setText("");
        setValidationText("");

        setLegalData(mockResponse);
        setAllSources(mockResponse);

        setTimeout(() => {
          const assistantMessage: Message = {
            role: "assistant",
            content: mockResponse.answer.text,
          };
          setMessages([...messages, assistantMessage]);
        }, 1000);
      }
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {!isOpen && (
        <Image
          className="absolute -top-0 w-1/2 left-0 translate-x-1/2 object-contain max-h-[200px]"
          src="/logo-compact-blauw.svg"
          alt="Logo Rijksoverheid"
          width={500}
          height={500}
        />
      )}
      {/* Header with buttons */}
      {!isOpen && (
        <div className="absolute top-20 left-4 z-10 flex gap-4 items-center">
          <Button variant="ghost" className="flex items-center gap-2">
            <Menu className="h-6 w-6" />
            <span>Menu</span>
          </Button>
          <Button
            variant="outline"
            className="flex items-center gap-2 p-6"
            onClick={handleNewChat}
          >
            <SquarePen className="h-6 w-6" />
            <span>Nieuw gesprek</span>
          </Button>
        </div>
      )}
      {/* Main content area */}
      <div className="flex flex-col h-full w-full px-8 overflow-hidden">
        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden justify-center items-center">
          {!isChatOpen ? (
            <div className="flex flex-col items-center justify-center">
              <MainContent
                messages={messages}
                handleNewChat={handleNewChat}
                chatStarted={isChatOpen}
              />
            </div>
          ) : (
            <div className="flex flex-col h-full overflow-hidden w-full">
              <MainContent
                messages={messages}
                handleNewChat={handleNewChat}
                chatStarted={isChatOpen}
              />
            </div>
          )}

          <div
            className={cn(
              "p-4 w-full flex justify-center transition-all duration-500"
            )}
          >
            <ChatInput
              text={text}
              setText={setText}
              handleKeyDown={handleKeyDown}
              isOpen={isOpen}
              validationText={validationText}
              dossierId={dossierId}
              setDossierId={setDossierId}
            />
          </div>
        </div>

        {/* Disclaimer at the bottom */}
        {!isOpen && (
          <div className="pb-6">
            <Disclaimer />
          </div>
        )}
      </div>
      <SourcesSidebar />
    </div>
  );
}
