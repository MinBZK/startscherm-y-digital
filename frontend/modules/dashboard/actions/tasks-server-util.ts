"use server";

import tasksData from "@/dummydata/data_tasks.json";
import { Task } from "@/lib/types";
import { API_BASE_URL, API_ENDPOINTS } from "../lib/api-config";
import { buildAuthHeaders } from "./auth-headers";

process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

export async function getTasksData(): Promise<Task[]> {
  if (process.env.NEXT_PUBLIC_ENV === "development") {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return tasksData as Task[];
  }

  const URL = `${API_BASE_URL}${API_ENDPOINTS.tasks.getTasks}`;

  const response = await fetch(URL, {
    method: "GET",
    headers: await buildAuthHeaders({ "Content-Type": "application/json" }),
  });

  if (response.ok) {
    const data = await response.json();
    return data as Task[];
  } else {
    console.error("Error getting tasks data:", response.statusText);
  }

  return [];
}
