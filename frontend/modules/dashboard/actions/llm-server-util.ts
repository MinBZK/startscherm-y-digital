"use server";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { buildAuthHeaders } from "./auth-headers";

interface Params {
  message: string;
}

export interface LLMResponse {
  message: string;
}

export async function getLLMResponse({
  message,
}: Params): Promise<LLMResponse> {
  if (!message.trim()) {
    throw new Error("Message cannot be empty");
  }
  const res = await fetch(`${API_BASE_URL}${API_ENDPOINTS.llm.query}`, {
    method: "POST",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      message,
      // session id is required, not setting it right now.
      session_id: "",
    }),
  });
  if (!res.ok) {
    throw new Error(
      `Failed to fetch search results: [${res.status}]: ${res.statusText}`
    );
  }
  return res.json();
}
