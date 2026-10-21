import { useEffect, useState } from "react";

import { pcApi, type PcClient, type PcJob } from "./api";

const stateLabels = { running: "处理中（首次需加载模型）", succeeded: "静态任务完成", cancelled: "已取消", failed: "任务失败" };

export function PcWorkbench({ client = pcApi }: { client?: PcClient }) {
  const [image, setImage] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [question, setQuestion] = useState("");
  const [consent, setConsent] = useState(false);
  const [job, setJob] = useState<PcJob | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const busy = sending || job?.state === "running";

  useEffect(() => {
    if (!job || job.state !== "running") return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await client.get(job.job_id);
        if (!stopped) { setJob(next); setError(null); }
      } catch {
        if (!stopped) setError("任务状态不可用；结果不再可信，请重试查询或取消");
      }
      if (!stopped) timer = setTimeout(() => void poll(), 750);
    };
    timer = setTimeout(() => void poll(), 300);
    return () => { stopped = true; clearTimeout(timer); };
  }, [client, job?.job_id, job?.state]);

  const selectImage = (file?: File) => {
    setImage(null); setJob(null); setError(null);
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 1024 * 1024) {
      setError("请选择不超过 1 MiB 的 JPEG 或 PNG 图片"); return;
    }
    const reader = new FileReader();
    setSending(true);
    reader.onload = () => { setImage(String(reader.result)); setSending(false); };
    reader.onerror = () => { setError("图片读取失败"); setSending(false); };
    reader.readAsDataURL(file);
  };

  const submit = async (kind: "locate" | "dialogue") => {
    setSending(true); setJob(null); setError(null);
    try {
      const next = kind === "locate"
        ? await client.submit({ kind, query: query.trim(), image_base64: image!.split(",")[1] ?? "" })
        : await client.submit({ kind, question: question.trim(), allow_cloud_text: true });
      setJob(next);
    } catch { setError("请求未确认：请检查本地服务是否启用电脑任务，或是否有任务正在运行；勿连续重复提交"); }
    finally { setSending(false); if (kind === "dialogue") setConsent(false); }
  };

  const cancel = async () => {
    if (!job) return;
    setSending(true);
    try { setJob(await client.cancel(job.job_id)); setError(null); }
    catch { setError("取消未确认，后台任务可能仍在运行"); }
    finally { setSending(false); }
  };
  const result = !error && job?.state === "succeeded" ? job.result : null;

  const recover = async () => {
    setSending(true); setImage(null); setJob(null);
    try { setJob(await client.active()); setError(null); }
    catch { setError("无法查询后台任务，请检查本地服务"); }
    finally { setSending(false); }
  };

  return <section className="panel pc-workbench" aria-labelledby="pc-title">
    <div className="panel__head"><div><span className="kicker">PC EVALUATION / NO HARDWARE</span><h2 id="pc-title">电脑模型样机</h2></div><span className="tag">静态图片 · 非实时</span></div>
    <p className="control-note">选图仅发送到本机 LocateAnything。没有 ToF，距离未知；不提供伸手深度或安全行进指令。每次任务独立加载模型。</p>
    <div className="pc-columns">
      <div className="pc-form">
        <label>本机图片<input type="file" accept="image/jpeg,image/png" disabled={busy} onChange={event => selectImage(event.target.files?.[0])} /></label>
        <label>找物描述（建议英文）<input value={query} maxLength={160} disabled={busy} onChange={event => { setQuery(event.target.value); setJob(null); }} /></label>
        <button disabled={busy || !image || !query.trim()} onClick={() => void submit("locate")}>本机找物</button>
        <label>对话问题<input value={question} maxLength={1000} disabled={busy} onChange={event => { setQuestion(event.target.value); setConsent(false); setJob(null); }} /></label>
        <label className="pc-consent"><input type="checkbox" checked={consent} disabled={busy} onChange={event => setConsent(event.target.checked)} />同意将这次问题文字发送到 DeepSeek（不发送图片，可能产生 API 费用）</label>
        <button disabled={busy || !consent || !question.trim()} onClick={() => void submit("dialogue")}>发送文字对话</button>
        <button disabled={!job || job.state !== "running" || sending} onClick={() => void cancel()}>取消电脑任务</button>
        <button disabled={busy} onClick={() => void recover()}>查询后台任务</button>
      </div>
      <div>
        {image ? <div className="pc-image"><img src={image} alt="用户选定的静态测试图片" />{job?.kind === "locate" && result?.boxes?.map((box, i) => <span className="pc-box" key={i} aria-label={`目标 ${i + 1}`} style={{ left: `${box[0] * 100}%`, top: `${box[1] * 100}%`, width: `${(box[2] - box[0]) * 100}%`, height: `${(box[3] - box[1]) * 100}%` }}>{i + 1}</span>)}</div> : <div className="empty-state">选择图片后可运行本机模型，不自动打开相机</div>}
        <p role="status" aria-live="polite">{job ? stateLabels[job.state] : "等待明确操作"}</p>
        {error && <p role="alert">{error}</p>}
        {job?.state === "failed" && <p role="alert">模型或服务不可用：{job.error}；未获得有效结果</p>}
        {result?.boxes && <p>检测到 {result.boxes.length} 个候选；模型推理 {result.inference_ms} ms（不含冷启动）。距离：未知；未确认拿取。</p>}
        {result?.text && <div className="pc-answer"><p>DeepSeek 文字回复（没有现场视觉/测距信息，不作为行进指令）</p><p>{result.text}</p></div>}
      </div>
    </div>
  </section>;
}
