import type { CommandAction, CommandReceipt, StatusSnapshot } from "./types";

const TIMEOUT_MS = 2500;

async function request(path: string, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(path, { ...init, signal: controller.signal, credentials: "same-origin" });
  } finally {
    window.clearTimeout(timeout);
  }
}

export interface DashboardClient {
  status(): Promise<StatusSnapshot>;
  command(action: CommandAction): Promise<CommandReceipt>;
}

export const api: DashboardClient = {
  async status() {
    const response = await request("/api/v1/status", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`status_${response.status}`);
    const value = (await response.json()) as StatusSnapshot;
    if (value.schema !== "xg.status.v1") throw new Error("unsupported_status_schema");
    return value;
  },
  async command(action) {
    const response = await request("/api/v1/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ action }),
    });
    if (!response.ok) throw new Error(`command_${response.status}`);
    return (await response.json()) as CommandReceipt;
  },
};
