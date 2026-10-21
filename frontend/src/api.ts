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

export interface PcResult {
  boxes?: [number, number, number, number][];
  inference_ms?: number;
  text?: string;
  distance_m?: null;
  grasp_confirmed?: false;
  query_en?: string;
  model_reused?: boolean;
}

export interface PcJob {
  job_id: string;
  kind: "locate" | "dialogue";
  state: "running" | "succeeded" | "cancelled" | "failed";
  result: PcResult | null;
  error: string | null;
}

export type PcRequest = { kind: "locate"; query: string; image_base64: string; source?: "file" | "pc_camera"; allow_cloud_translation?: boolean }
  | { kind: "dialogue"; question: string; allow_cloud_text: true };

export interface PcClient {
  active(): Promise<PcJob | null>;
  submit(value: PcRequest): Promise<PcJob>;
  get(id: string): Promise<PcJob>;
  cancel(id: string): Promise<PcJob>;
}

async function pcRequest(path: string, value?: PcRequest | Record<string, never>): Promise<PcJob> {
  const response = await request(path, value ? {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(value),
  } : undefined);
  if (!response.ok) throw new Error(`pc_${response.status}`);
  return await response.json() as PcJob;
}

export const pcApi: PcClient = {
  async active() {
    const response = await request("/api/v1/pc/active");
    if (!response.ok) throw new Error(`pc_${response.status}`);
    return (await response.json() as { job: PcJob | null }).job;
  },
  submit: value => pcRequest("/api/v1/pc/jobs", value),
  get: id => pcRequest(`/api/v1/pc/jobs/${encodeURIComponent(id)}`),
  cancel: id => pcRequest(`/api/v1/pc/jobs/${encodeURIComponent(id)}/cancel`, {}),
};
