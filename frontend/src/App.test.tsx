import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import type { DashboardClient } from "./api";
import type { StatusSnapshot } from "./types";

function snapshot(overrides: Partial<StatusSnapshot> = {}): StatusSnapshot {
  return {
    schema: "xg.status.v1", revision: 1, generated_ns: "1", mode: "offline",
    link: { state: "disconnected", reason: "not_connected", session_id: null, boot_id: null, capabilities: { clock: false, tof: false, imu: false, button: false, camera: false, haptic: false }, clock: { state: "unknown", uncertainty_ms: null } },
    frame: { state: "absent", source: "none", frame_id: null, age_ms: null, width: null, height: null, calibration_id: null },
    tof: { state: "unknown", valid_zones: 0, total_zones: 0, zones_mm: [] },
    imu: { state: "unknown", sample_id: null }, calibration: { state: "missing", calibration_id: null }, commands: [], logs: [], ...overrides,
  };
}

function client(value: StatusSnapshot): DashboardClient {
  return { status: vi.fn().mockResolvedValue(value), command: vi.fn().mockResolvedValue({ request_id: "7", action: "safe_stop", state: "pending" }) };
}

describe("dashboard safety states", () => {
  it("renders offline and unknown without inventing sensor values", () => {
    render(<App initial={snapshot()} client={client(snapshot())} polling={false} />);
    expect(screen.getByText("眼镜未连接")).toBeInTheDocument();
    expect(screen.getByText("等待多区 ToF 数据")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "启动视频流" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /停止输出/ })).toBeDisabled();
  });

  it("announces submission as pending instead of applied", async () => {
    const ready = snapshot({ mode: "live", link: { state: "ready", reason: "connected_clock_estimated", session_id: "3", boot_id: "4", capabilities: { clock: true, tof: true, imu: true, button: true, camera: true, haptic: false }, clock: { state: "estimated", uncertainty_ms: 2.2 } } });
    const mockClient = client(ready);
    render(<App initial={ready} client={mockClient} polling={false} />);
    await userEvent.click(screen.getByRole("button", { name: "启动视频流" }));
    expect(mockClient.command).toHaveBeenCalledWith("start_stream");
    expect(await screen.findByText("请求 #7 已提交，等待设备确认")).toBeInTheDocument();
    expect(screen.queryByText("设备已确认")).not.toBeInTheDocument();
  });

  it("shows rejected command and replay source explicitly", () => {
    const value = snapshot({ mode: "replay", commands: [{ request_id: "9", action: "stop_stream", state: "rejected", at_ns: "10" }], frame: { state: "fresh", source: "replay", frame_id: 5, age_ms: 42, width: 640, height: 480, calibration_id: null } });
    render(<App initial={value} client={client(value)} polling={false} />);
    expect(screen.getByText("回放")).toBeInTheDocument();
    expect(screen.getByText("已拒绝")).toBeInTheDocument();
    expect(screen.queryByText("设备已确认")).not.toBeInTheDocument();
  });
});
