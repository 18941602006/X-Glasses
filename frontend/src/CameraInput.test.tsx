import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CameraInput } from "./CameraInput";

function camera() {
  const track = { stop: vi.fn(), addEventListener: vi.fn() };
  return { track, stream: { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream };
}
function props() {
  return { enabled: true, busy: false, stopSignal: 0, onFrame: vi.fn().mockResolvedValue(true), onActivity: vi.fn(), onCancel: vi.fn() };
}
let getUserMedia: ReturnType<typeof vi.fn>;
beforeEach(() => {
  getUserMedia = vi.fn();
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
});

describe("camera lifecycle", () => {
  it("does not request camera on mount; opens video only without audio", async () => {
    const input = props(); const media = camera(); getUserMedia.mockResolvedValue(media.stream);
    const view = render(<CameraInput {...input} />);
    expect(getUserMedia).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "开启摄像头" }));
    expect(getUserMedia).toHaveBeenCalledWith(expect.objectContaining({ audio: false }));
    expect(screen.getByLabelText("本机摄像头实时预览")).toBeVisible();
    view.unmount();
    expect(media.track.stop).toHaveBeenCalled();
  });

  it("reports permission rejection without pretending video is running", async () => {
    getUserMedia.mockRejectedValue(new DOMException("denied", "NotAllowedError"));
    render(<CameraInput {...props()} />);
    await userEvent.click(screen.getByRole("button", { name: "开启摄像头" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("相机权限被拒绝");
    expect(screen.getByLabelText("本机摄像头实时预览")).not.toBeVisible();
  });

  it("stops a late permission result after the user already closed", async () => {
    let resolve!: (value: MediaStream) => void;
    getUserMedia.mockReturnValue(new Promise<MediaStream>(done => { resolve = done; }));
    const media = camera(); render(<CameraInput {...props()} />);
    await userEvent.click(screen.getByRole("button", { name: "开启摄像头" }));
    await userEvent.click(screen.getByRole("button", { name: "关闭摄像头" }));
    await act(async () => resolve(media.stream));
    expect(media.track.stop).toHaveBeenCalled();
    expect(screen.getByLabelText("本机摄像头实时预览")).not.toBeVisible();
  });

  it("captures a frame and never queues more frames while a job is pending", async () => {
    const input = props(); const media = camera(); getUserMedia.mockResolvedValue(media.stream);
    let resolve!: (value: boolean) => void;
    input.onFrame.mockReturnValue(new Promise<boolean>(done => { resolve = done; }));
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({ drawImage: vi.fn() } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, "toDataURL").mockReturnValue("data:image/jpeg;base64,abcd");
    render(<CameraInput {...input} />);
    await userEvent.click(screen.getByRole("button", { name: "开启摄像头" }));
    const video = screen.getByLabelText("本机摄像头实时预览");
    Object.defineProperty(video, "videoWidth", { configurable: true, value: 640 });
    Object.defineProperty(video, "videoHeight", { configurable: true, value: 480 });
    await userEvent.click(screen.getByRole("button", { name: "开始连续找物" }));
    expect(input.onFrame).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "停止连续找物" }));
    await act(async () => resolve(true));
    expect(input.onFrame).toHaveBeenCalledTimes(1);
    expect(input.onCancel).toHaveBeenCalled();
  });

  it("does not send an empty video frame", async () => {
    const input = props(); getUserMedia.mockResolvedValue(camera().stream);
    render(<CameraInput {...input} />);
    await userEvent.click(screen.getByRole("button", { name: "开启摄像头" }));
    await userEvent.click(screen.getByRole("button", { name: "取一帧找物" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("视频帧尚未就绪"));
    expect(input.onFrame).not.toHaveBeenCalled();
  });

  it("releases the stream when the page becomes hidden", async () => {
    const input = props(); const media = camera(); getUserMedia.mockResolvedValue(media.stream);
    render(<CameraInput {...input} />);
    await userEvent.click(screen.getByRole("button", { name: "开启摄像头" }));
    const hidden = vi.spyOn(document, "hidden", "get").mockReturnValue(true);
    act(() => { document.dispatchEvent(new Event("visibilitychange")); });
    expect(media.track.stop).toHaveBeenCalled();
    expect(input.onCancel).toHaveBeenCalled();
    hidden.mockRestore();
  });
});
