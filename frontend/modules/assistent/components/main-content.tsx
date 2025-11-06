import { ChatView } from "./chat-view";
import { InitialHomepageView } from "./initial-homepage-view";
import { Message } from "@/lib/types";

interface MainContentProps {
  messages: Message[];
  handleNewChat: () => void;
  chatStarted: boolean;
}

// Main content component that changes based on chat state
export const MainContent = ({
  messages,
  handleNewChat,
  chatStarted,
}: MainContentProps) => {
  return (
    <div
      className={`flex flex-col overflow-hidden transition-all duration-500 ${
        chatStarted ? "h-full" : "h-fit"
      }`}
    >
      {!chatStarted && <InitialHomepageView />}
      {chatStarted && (
        <ChatView messages={messages} handleNewChat={handleNewChat} />
      )}
    </div>
  );
};
