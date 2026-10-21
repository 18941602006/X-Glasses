import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PcWorkbench } from "./PcWorkbench";
import type { PcClient, PcJob } from "./api";

const running: PcJob = { job_id: "abc", kind: "locate", state: "running", result: null, error: null };
function client(): PcClient {
  return { active: vi.fn().mockResolvedValue(null), submit: vi.fn().mockResolvedValue(running), get: vi.fn().mockResolvedValue(running), cancel: vi.fn().mockResolvedValue({ ...running, state: "cancelled" }) };
}
async function choose() {
  await userEvent.upload(screen.getByLabelText("本机图片"), new File(["image"], "sample.png", { type: "image/png" }));
  await waitFor(() => expect(screen.getByRole("img")).toBeInTheDocument());
  await userEvent.type(screen.getByLabelText("找物描述（建议英文）"), "cat");
}

describe("PC workbench", () => {
  it("does not submit automatically or send dialogue without consent", async () => {
    const api = client();
    render(<PcWorkbench client={api} />);
    await userEvent.type(screen.getByLabelText("对话问题"), "hello");
    expect(screen.getByRole("button", { name: "发送文字对话" })).toBeDisabled();
    expect(api.submit).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(screen.getByRole("button", { name: "发送文字对话" }));
    expect(api.submit).toHaveBeenCalledWith({ kind: "dialogue", question: "hello", allow_cloud_text: true });
    expect(screen.getByRole("checkbox")).not.toBeChecked();
  });

  it("uploads only selected image locally and cancels the actual job", async () => {
    const api = client();
    render(<PcWorkbench client={api} />);
    await choose();
    await userEvent.click(screen.getByRole("button", { name: "本机找物" }));
    expect(api.submit).toHaveBeenCalledWith({ kind: "locate", query: "cat", image_base64: expect.any(String) });
    expect(screen.getByLabelText("找物描述（建议英文）")).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "取消电脑任务" }));
    expect(api.cancel).toHaveBeenCalledWith("abc");
    expect(await screen.findByText("已取消")).toBeInTheDocument();
    expect(screen.queryByLabelText("目标 1")).not.toBeInTheDocument();
  });

  it("shows static boxes with unknown distance and clears after query change", async () => {
    const api = client();
    vi.mocked(api.get).mockResolvedValue({ ...running, state: "succeeded", result: { boxes: [[0, 0, 1, 1]], inference_ms: 12 } });
    render(<PcWorkbench client={api} />);
    await choose();
    await userEvent.click(screen.getByRole("button", { name: "本机找物" }));
    expect(await screen.findByLabelText("目标 1")).toBeInTheDocument();
    expect(screen.getByText(/距离：未知；未确认拿取/)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("找物描述（建议英文）"), "s");
    expect(screen.queryByLabelText("目标 1")).not.toBeInTheDocument();
  });

  it("keeps errors visible without fabricating results", async () => {
    const api = client();
    vi.mocked(api.submit).mockRejectedValue(new Error("unavailable"));
    render(<PcWorkbench client={api} />);
    await choose();
    await userEvent.click(screen.getByRole("button", { name: "本机找物" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("请求未确认");
    expect(screen.queryByLabelText("目标 1")).not.toBeInTheDocument();
  });

  it("recovers a running task after a lost receipt and clears unrelated image", async () => {
    const api = client();
    vi.mocked(api.active).mockResolvedValue(running);
    render(<PcWorkbench client={api} />);
    await choose();
    await userEvent.click(screen.getByRole("button", { name: "查询后台任务" }));
    expect(api.active).toHaveBeenCalled();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "取消电脑任务" })).toBeEnabled();
  });
});
