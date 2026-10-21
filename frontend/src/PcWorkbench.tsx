import { useEffect, useRef, useState } from "react";

import { pcApi, type PcClient, type PcJob, type PcRequest } from "./api";
import { CameraInput } from "./CameraInput";

const stateLabels = { running: "处理中（首次需加载模型）", succeeded: "定位帧任务完成", cancelled: "已取消", failed: "任务失败" };
const hasChinese = (text: string) => /[\u3400-\u9fff]/u.test(text);

export function PcWorkbench({ client = pcApi }: { client?: PcClient }) {
  const [image, setImage] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [question, setQuestion] = useState("");
  const [consent, setConsent] = useState(false);
  const [translateConsent, setTranslateConsent] = useState(false);
  const [job, setJob] = useState<PcJob | null>(null);
  const [sending, setSending] = useState(false);
  const [looping, setLooping] = useState(false);
  const [stopSignal, setStopSignal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [frameLabel, setFrameLabel] = useState("选定图片");
  const epoch = useRef(0);
  const mounted = useRef(true);
  const currentJob = useRef<PcJob | null>(null);
  const cameraTask = useRef(false);
  const busy = sending || looping || job?.state === "running";
  const canLocate = !!query.trim() && (!hasChinese(query) || translateConsent);

  const updateJob = (next: PcJob | null) => { currentJob.current = next; setJob(next); };
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; epoch.current++; };
  }, []);

  const follow = async (first: PcJob, version: number): Promise<boolean> => {
    let next = first;
    while (mounted.current && version === epoch.current) {
      updateJob(next);
      if (next.state !== "running") return next.state === "succeeded";
      await new Promise(resolve => setTimeout(resolve, 350));
      if (!mounted.current || version !== epoch.current) return false;
      next = await client.get(first.job_id);
    }
    return false;
  };
  const run = async (request: PcRequest): Promise<boolean> => {
    const version = ++epoch.current;
    setSending(true); updateJob(null); setError(null);
    try {
      const receipt = await client.submit(request);
      if (!mounted.current || version !== epoch.current) {
        if (receipt.state === "running") await client.cancel(receipt.job_id);
        return false;
      }
      setSending(false);
      return await follow(receipt, version);
    } catch {
      if (mounted.current && version === epoch.current) setError("请求或任务状态未确认：请检查本地服务，查询后台任务后重试；未得到有效定位结果");
      return false;
    } finally {
      if (mounted.current && version === epoch.current) setSending(false);
    }
  };
  const locate = async (data: string, source: "file" | "pc_camera") => {
    cameraTask.current = source === "pc_camera";
    setImage(data); setFrameLabel(source === "pc_camera" ? `定位取帧 ${new Date().toLocaleTimeString()}（不是当前视频）` : "选定图片（非实时）");
    return run({ kind: "locate", query: query.trim(), image_base64: data.split(",")[1] ?? "", source, allow_cloud_translation: translateConsent });
  };
  const cancel = async () => {
    epoch.current++; setStopSignal(value => value + 1); setLooping(false); setSending(false);
    const active = currentJob.current;
    if (!active || active.state !== "running") return;
    try { updateJob(await client.cancel(active.job_id)); setError(null); }
    catch { setError("取消未确认，后台任务可能仍在运行"); }
  };
  const cancelCamera = () => { if (cameraTask.current) void cancel(); };

  const selectImage = (file?: File) => {
    setImage(null); updateJob(null); setError(null);
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 1024 * 1024) {
      setError("请选择不超过 1 MiB 的 JPEG 或 PNG 图片"); return;
    }
    const reader = new FileReader();
    setSending(true);
    reader.onload = () => { if (mounted.current) { setImage(String(reader.result)); setFrameLabel("选定图片（非实时）"); setSending(false); } };
    reader.onerror = () => { if (mounted.current) { setError("图片读取失败"); setSending(false); } };
    reader.readAsDataURL(file);
  };
  const recover = async () => {
    const version = ++epoch.current;
    setSending(true); setImage(null); updateJob(null); cameraTask.current = false;
    try {
      const active = await client.active();
      setSending(false); setError(null);
      if (active) await follow(active, version);
    } catch { if (mounted.current) setError("无法查询后台任务，请检查本地服务"); }
    finally { if (mounted.current && version === epoch.current) setSending(false); }
  };
  const result = !error && job?.state === "succeeded" ? job.result : null;

  return <section className="panel pc-workbench" aria-labelledby="pc-title">
    <div className="panel__head"><div><span className="kicker">PC EVALUATION / NO HARDWARE</span><h2 id="pc-title">电脑模型样机</h2></div><span className="tag">实时预览 · 异步定位</span></div>
    <p className="control-note">图片和视频只由本机 LocateAnything 识别；中文描述经你同意后仅把文字发给 DeepSeek 翻译。没有 ToF，距离未知，不作为安全行进指令。</p>
    <div className="pc-columns">
      <div className="pc-form">
        <label>本机图片<input type="file" accept="image/jpeg,image/png" disabled={busy} onChange={event => selectImage(event.target.files?.[0])} /></label>
        <label>找物描述（中文或英文）<input value={query} maxLength={160} disabled={busy} onChange={event => { setQuery(event.target.value); setTranslateConsent(false); updateJob(null); }} /></label>
        <label className="pc-consent"><input type="checkbox" checked={translateConsent} disabled={busy} onChange={event => setTranslateConsent(event.target.checked)} />同意仅发送找物描述给 DeepSeek 翻译为英语；不发送图片/视频。同一描述连续找物复用翻译，可能产生文字 API 费用。</label>
        <button disabled={busy || !image || !canLocate} onClick={() => { if (image) void locate(image, "file"); }}>本机找物</button>
        <label>对话问题<input value={question} maxLength={1000} disabled={busy} onChange={event => { setQuestion(event.target.value); setConsent(false); updateJob(null); }} /></label>
        <label className="pc-consent"><input type="checkbox" checked={consent} disabled={busy} onChange={event => setConsent(event.target.checked)} />同意将这次问题文字发送到 DeepSeek（不发送图片，可能产生 API 费用）</label>
        <button disabled={busy || !consent || !question.trim()} onClick={() => {
          cameraTask.current = false; setConsent(false);
          void run({ kind: "dialogue", question: question.trim(), allow_cloud_text: true });
        }}>发送文字对话</button>
        <button disabled={!job || job.state !== "running"} onClick={() => void cancel()}>取消电脑任务</button>
        <button disabled={busy} onClick={() => void recover()}>查询后台任务</button>
      </div>
      <div>
        <CameraInput enabled={canLocate} busy={busy} stopSignal={stopSignal} onFrame={data => locate(data, "pc_camera")} onActivity={setLooping} onCancel={cancelCamera} />
        {image ? <><h3>{frameLabel}</h3><div className="pc-image"><img src={image} alt="用户选定的静态测试图片或定位取帧" onError={() => setError("浏览器未能解码图片，请换成有效的 JPEG/PNG；尚未确认预览成功")} />{job?.kind === "locate" && result?.boxes?.map((box, i) => <span className="pc-box" key={i} aria-label={`目标 ${i + 1}`} style={{ left: `${box[0] * 100}%`, top: `${box[1] * 100}%`, width: `${(box[2] - box[0]) * 100}%`, height: `${(box[3] - box[1]) * 100}%` }}>{i + 1}</span>)}</div></> : <div className="empty-state">选图，或开启摄像头后取帧找物</div>}
        <p role="status" aria-live="polite">{job ? stateLabels[job.state] : "等待明确操作"}</p>
        {error && <p role="alert">{error}</p>}
        {job?.state === "failed" && <p role="alert">模型/翻译或服务不可用：{job.error}；未获得有效结果</p>}
        {result?.boxes && <><p>识别英语：{result.query_en ?? query}；模型{result.model_reused ? "已复用" : "首次加载"}。</p><p>检测到 {result.boxes.length} 个候选；模型推理 {result.inference_ms} ms（不含冷启动）。距离：未知；未确认拿取。</p></>}
        {result?.text && <div className="pc-answer"><p>DeepSeek 文字回复（没有现场视觉/测距信息，不作为行进指令）</p><p>{result.text}</p></div>}
      </div>
    </div>
  </section>;
}
