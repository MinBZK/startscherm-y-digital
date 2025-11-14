"use client";

import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Bot, Loader2Icon, Send } from "lucide-react";
import {
  useState,
  useEffect,
  useLayoutEffect,
  useRef,
  useCallback,
} from "react";
import Markdown from "react-markdown";
import { getLLMResponse, LLMResponse } from "../actions/llm-server-util";

interface Message {
  id: string;
  text: string;
  isBot: boolean;
}

export function LLMChat() {
  // Current input
  const [inputMessage, setInputMessage] = useState("");
  // Submitted input
  const [query, setQuery] = useState("");
  // All chat messages
  const [messages, setMessages] = useState<Message[]>([]);

  // Data for the current query.
  const { data, error, isLoading } = useQuery<LLMResponse>({
    queryKey: ["llm-search", query],
    queryFn: () => getLLMResponse({ message: query }),
    enabled: !!query.trim(),
  });

  useEffect(() => {
    if (data && query.trim()) {
      setMessages((prev) => [
        ...prev,
        {
          id: `llm-${Date.now()}`,
          text: data.message,
          isBot: true,
        },
      ]);
    }
  }, [data, query]);

  // Scroll to last user message when messages change
  const { setMessageRef } = useScrollDownToLastUserMessage(messages);

  // Scroll to the loading indicator when loading
  const loadingRef = useRef<HTMLDivElement>(null);
  // Scroll the indicator into view when it appears.
  useEffect(() => {
    if (loadingRef.current && isLoading) {
      loadingRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputMessage.trim()) {
      return;
    }

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        text: inputMessage.trim(),
        isBot: false,
      },
    ]);

    // Update query to trigger React Query
    setQuery(inputMessage.trim());

    // Clear input
    setInputMessage("");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div
        className={cn("overflow-y-auto -mb-4", {
          "flex-1": messages.length > 0 || isLoading,
        })}
      >
        <div
          className={cn("flex flex-col gap-4 items-center mt-32", {
            hidden: messages.length > 0 || isLoading,
          })}
        >
          <div className="flex items-center justify-center size-16 rounded-full bg-hemelblauw/10">
            <Bot className="text-hemelblauw" size={32} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Wat kan ik voor je betekenen?
          </h2>
        </div>
        {error ? (
          <div className="mx-auto w-fit bg-red-100 rounded text-red-800 px-3 py-2 mt-4">
            Er is een fout opgetreden ({error.message})
          </div>
        ) : null}

        <div className="flex-1 px-2 max-w-2xl mx-auto space-y-4 pb-10 w-full py-4">
          {messages.length === 0
            ? null
            : messages.map(({ id, text, isBot }, index) => (
                <article
                  key={id}
                  className={cn("flex", { "justify-end": !isBot })}
                  ref={(node: HTMLDivElement) => setMessageRef(index, node)}
                >
                  <div
                    className={cn({
                      "bg-hemelblauw/10 px-3 py-2 rounded-lg max-w-9/12 rounded-br-none":
                        !isBot,
                    })}
                  >
                    {isBot ? (
                      <div className="prose">
                        <Markdown>{text}</Markdown>
                      </div>
                    ) : (
                      text
                    )}
                  </div>
                </article>
              ))}

          {isLoading ? (
            <div
              className="flex items-center gap-1 text-muted-foreground"
              ref={loadingRef}
            >
              <Loader2Icon className="animate-spin flex-none" size={12} />
              Aan het denken...
            </div>
          ) : null}
        </div>
      </div>

      <div className="pb-4 flex-none max-w-2xl mx-auto w-full">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            className={cn(
              "w-full pr-12 bg-white rounded-full py-3 pl-6 border border-gray-200",
              "focus:ring-2 focus:ring-ring/50 outline-none focus:border-ring"
            )}
            disabled={isLoading}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Stel hier je vraag..."
            value={inputMessage}
          />
          <button
            aria-label="Verzenden"
            className="absolute right-2 cursor-pointer text-donkerblauw size-9 flex items-center justify-center transition-colors rounded-full hover:bg-hemelblauw/5"
            disabled={isLoading || !inputMessage.trim()}
            type="submit"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}

/**
 * Hook that automatically scrolls the last user message into view, prefering the top of the scroll container.
 * Generally this means the chat is always scrolled down to the last message, unless the last bot message is
 * very large. In that case, the last user message will be kept in view, and the user can scroll down to see
 * the rest of the bot message.
 *
 * @returns a function to set the ref of a message element
 */
export function useScrollDownToLastUserMessage(messages: Message[]) {
  const listRef = useRef<HTMLDivElement[]>([]);
  const containerRef = useRef<Element | null>(null);

  useLayoutEffect(() => {
    // Whenever the messages change, scroll the last user message to the top of the container.
    const index = getLastIndexOf(messages, ({ isBot }) => !isBot);

    if (index <= -1 || !listRef.current[index]) {
      // No user message found
      return;
    }

    const msgEl = listRef.current[index];

    if (!containerRef.current) {
      // Find the nearest scrolled container. (could be null if there is no scrolling yet)
      containerRef.current = getNearestScrolledParent(msgEl);
    }

    if (
      containerRef.current &&
      msgEl.getBoundingClientRect().top <=
        containerRef.current.getBoundingClientRect().top
    ) {
      // The user already scrolled past the message, it is currently above the visible area.
      // We would scroll up to show it, which is not desired. We only scroll down.
      return;
    }

    if (containerRef.current) {
      // We have a scroll container
      // Manual scroll using the container reference
      const containerRect = containerRef.current.getBoundingClientRect();
      const msgRect = msgEl.getBoundingClientRect();
      const scrollTop =
        containerRef.current.scrollTop + (msgRect.top - containerRect.top);

      containerRef.current.scrollTo({
        top: scrollTop,
        behavior: "smooth",
      });
    } else {
      // Fallback for when no container is found - scroll to element directly
      // This should be the default, but sadly container "nearest" is not supported in all browsers.
      // In browsers where "nearest" is not supported, this might scroll multiple containers unintentionally.
      msgEl.scrollIntoView({
        behavior: "smooth",
        block: "start",
        // @ts-expect-error - not implemented in all browsers
        container: "nearest",
      });
    }
  }, [messages]);

  const setMessageRef = useCallback(
    (index: number, node: HTMLDivElement | null) => {
      if (node) {
        listRef.current[index] = node;
      }
    },
    []
  );

  return {
    setMessageRef,
  };
}

/**
 * Find the last index in an array that matches a predicate.
 * @param arr The array to search.
 * @param predicate The predicate function.
 * @returns The last index that matches the predicate, or -1 if none found.
 */
function getLastIndexOf<T>(arr: T[], predicate: (value: T) => boolean) {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (predicate(arr[i])) {
      return i;
    }
  }
  return -1;
}

/**
 * Get the nearest parent element that has scrolling enabled.
 * @param node The starting element.
 * @returns The nearest scrolled parent element, or the document body if none found.
 */
function getNearestScrolledParent(node: Element): Element {
  let currentNode: Element | null = node;

  while (currentNode) {
    const overflowY =
      currentNode instanceof Element &&
      window.getComputedStyle(currentNode).overflowY;

    if (
      currentNode.scrollHeight >= currentNode.clientHeight &&
      !/^(visible|hidden)/.test(overflowY || "visible")
    ) {
      return currentNode;
    }

    currentNode = currentNode.parentElement;
  }

  return document.scrollingElement || document.body;
}
