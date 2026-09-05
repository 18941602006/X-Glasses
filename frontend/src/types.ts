export type SourceMode = "offline" | "live" | "replay";
export type LinkState = "disconnected" | "handshaking" | "ready";
export type DataState = "unknown" | "absent" | "fresh" | "stale" | "invalid";
export type CommandAction = "start_stream" | "stop_stream" | "cancel_haptic" | "safe_stop";
export type CommandState =
  | "pending"
  | "applied"
  | "rejected"
  | "expired"
  | "timeout"
  | "disconnected";

export interface Capabilities {
  clock: boolean;
  tof: boolean;
  imu: boolean;
  button: boolean;
  camera: boolean;
  haptic: boolean;
}

export interface CommandRecord {
  request_id: string;
  action: CommandAction;
  state: CommandState;
  at_ns: string;
}

export interface StatusSnapshot {
  schema: "xg.status.v1";
  revision: number;
  generated_ns: string;
  mode: SourceMode;
  link: {
    state: LinkState;
    reason: string;
    session_id: string | null;
    boot_id: string | null;
    capabilities: Capabilities;
    clock: { state: "unknown" | "estimated" | "stale"; uncertainty_ms: number | null };
  };
  frame: {
    state: DataState;
    source: "none" | "live" | "replay" | "synthetic";
    frame_id: number | null;
    age_ms: number | null;
    width: number | null;
    height: number | null;
    calibration_id: string | null;
  };
  tof: {
    state: DataState;
    valid_zones: number;
    total_zones: number;
    zones_mm: Array<number | null>;
  };
  imu: { state: DataState; sample_id: number | null };
  calibration: { state: "missing" | "loaded" | "invalid"; calibration_id: string | null };
  commands: CommandRecord[];
  logs: Array<{ level: "info" | "warning" | "error"; message: string; at_ns: string }>;
}

export interface CommandReceipt {
  request_id: string;
  action: CommandAction;
  state: "pending";
}
