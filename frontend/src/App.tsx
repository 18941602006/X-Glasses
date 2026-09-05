import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";

import { api, type DashboardClient } from "./api";
import type { CommandAction, CommandState, StatusSnapshot } from "./types";

const fallback: StatusSnapshot = {
  schema: "xg.status.v1",
  revision: 0,
  generated_ns: "0",
  mode: "offline",
  link: {
    state: "disconnected",
    reason: "not_connected",
    session_id: null,
    boot_id: null,
    capabilities: { clock: false, tof: false, imu: false, button: false, camera: false, haptic: false },
    clock: { state: "unknown", uncertainty_ms: null },
  },
  frame: { state: "absent", source: "none", frame_id: null, age_ms: null, width: null, height: null, calibration_id: null },
  tof: { state: "unknown", valid_zones: 0, total_zones: 0, zones_mm: [] },
  imu: { state: "unknown", sample_id: null },
  calibration: { state: "missing", calibration_id: null },
  commands: [],
  logs: [],
};

const labels: Record<CommandState, string> = {
  pending: "等待确认",
  applied: "设备已确认",
  rejected: "已拒绝",
  expired: "已过期",
  timeout: "确认超时",
  disconnected: "连接已断开",
};

const modeLabel = { offline: "离线", live: "实机", replay: "回放" } as const;

interface AppProps {
  client?: DashboardClient;
  initial?: StatusSnapshot;
  polling?: boolean;
}

function Metric({ label, value, tone = "neutral" }: { label: string; value: string; tone?: string }) {
  return <div className={`metric metric--${tone}`}><span>{label}</span><strong>{value}</strong></div>;
}

export function App({ client = api, initial = fallback, polling = true }: AppProps) {
  const [status, setStatus] = useState(initial);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("等待本地服务状态");
  const [sending, setSending] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const next = await client.status();
      setStatus(next);
      setNetworkError(null);
    } catch {
      setNetworkError("本地服务不可用；当前画面不是实时状态");
    }
  }, [client]);

  useEffect(() => {
    if (!polling) return;
    void refresh();
    const timer = window.setInterval(() => void refresh(), 1000);
    return () => window.clearInterval(timer);
  }, [polling, refresh]);

  const issue = async (action: CommandAction) => {
    setSending(true);
    try {
      const receipt = await client.command(action);
      setAnnouncement(`请求 #${receipt.request_id} 已提交，等待设备确认`);
      await refresh();
    } catch {
      setAnnouncement("请求未提交：设备或本地服务不可用");
    } finally {
      setSending(false);
    }
  };

  const ready = status.link.state === "ready" && !networkError;
  const zones = status.tof.zones_mm.slice(0, 64);
  const newestCommand = status.commands.at(-1);
  const linkText = ready ? "眼镜已连接" : "眼镜未连接";
  const frameAge = status.frame.age_ms == null ? "未知" : `${Math.round(status.frame.age_ms)} ms`;
  const tofValue = status.tof.total_zones
    ? `${status.tof.valid_zones} / ${status.tof.total_zones}`
    : "无数据";
  const capabilityList = useMemo(
    () => Object.entries(status.link.capabilities).filter(([, enabled]) => enabled).map(([name]) => name.toUpperCase()),
    [status.link.capabilities],
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand__mark">XG</span><div><p>X-GLASSES</p><span>LOCAL ASSIST CONSOLE</span></div></div>
        <div className="topbar__status">
          <span className={`mode mode--${status.mode}`}>{modeLabel[status.mode]}</span>
          <span className={`connection ${ready ? "is-ready" : "is-offline"}`}><i />{linkText}</span>
        </div>
      </header>

      <main id="main">
        <section className="hero" aria-labelledby="page-title">
          <div><p className="eyebrow">设备态势 / REV {status.revision}</p><h1 id="page-title">调试驾驶舱</h1><p>所有数据均标注来源与时效。未知状态不会被解释为安全。</p></div>
          <button className="safe-stop" disabled={!ready || sending} onClick={() => void issue("safe_stop")}>
            <span>停止输出</span><small>请求取消震动并停止视频流</small>
          </button>
        </section>

        {networkError && <div className="alert" role="alert">{networkError}</div>}
        <p className="sr-only" aria-live="polite">{announcement}</p>

        <section className="dashboard-grid" aria-label="设备状态面板">
          <article className="panel vision-panel">
            <div className="panel__head"><div><span className="kicker">CAMERA FEED</span><h2>视觉输入</h2></div><span className={`tag tag--${status.frame.state}`}>{status.frame.state}</span></div>
            <div className={`viewfinder viewfinder--${status.frame.state}`} aria-label="相机预览状态">
              <div className="reticle" aria-hidden="true"><span /><span /></div>
              <div className="viewfinder__message"><strong>{status.frame.state === "fresh" ? `帧 #${status.frame.frame_id}` : "没有可显示的实时画面"}</strong><span>来源：{status.frame.source}</span></div>
            </div>
            <div className="metric-row">
              <Metric label="帧龄" value={frameAge} tone={status.frame.state === "fresh" ? "good" : "warn"} />
              <Metric label="分辨率" value={status.frame.width ? `${status.frame.width} × ${status.frame.height}` : "未知"} />
              <Metric label="时钟误差" value={status.link.clock.uncertainty_ms == null ? "未知" : `±${status.link.clock.uncertainty_ms} ms`} />
            </div>
          </article>

          <article className="panel sensor-panel">
            <div className="panel__head"><div><span className="kicker">DEPTH MAP</span><h2>ToF 距离分区</h2></div><span className={`tag tag--${status.tof.state}`}>{status.tof.state}</span></div>
            <div className="tof-grid" aria-label={`ToF 有效分区 ${tofValue}`}>
              {zones.length ? zones.map((distance, index) => <span key={index} className={distance == null ? "zone zone--unknown" : "zone"} style={distance == null ? undefined : { "--zone-alpha": Math.max(0.16, 1 - distance / 2400).toFixed(2) } as CSSProperties} title={distance == null ? "未知" : `${distance} mm`} />) : <div className="empty-grid">等待多区 ToF 数据</div>}
            </div>
            <div className="metric-row"><Metric label="有效分区" value={tofValue} tone={status.tof.state === "fresh" ? "good" : "warn"} /><Metric label="IMU" value={status.imu.state} /><Metric label="标定" value={status.calibration.state === "loaded" ? status.calibration.calibration_id ?? "已加载" : "未完成"} tone={status.calibration.state === "loaded" ? "good" : "warn"} /></div>
          </article>

          <article className="panel control-panel">
            <div className="panel__head"><div><span className="kicker">CONTROL PLANE</span><h2>链路与控制</h2></div><span className="tag">localhost</span></div>
            <dl className="facts"><div><dt>链路状态</dt><dd>{status.link.state}</dd></div><div><dt>原因</dt><dd>{status.link.reason}</dd></div><div><dt>会话</dt><dd>{status.link.session_id ?? "—"}</dd></div><div><dt>能力</dt><dd>{capabilityList.length ? capabilityList.join(" · ") : "未声明"}</dd></div></dl>
            <div className="button-grid">
              <button disabled={!ready || !status.link.capabilities.camera || sending} onClick={() => void issue("start_stream")}>启动视频流</button>
              <button disabled={!ready || sending} onClick={() => void issue("stop_stream")}>停止视频流</button>
              <button disabled={!ready || sending} onClick={() => void issue("cancel_haptic")}>取消震动</button>
            </div>
            <p className="control-note">按钮只提交后端请求；必须收到设备 ACK 才能显示“设备已确认”。</p>
          </article>

          <article className="panel activity-panel">
            <div className="panel__head"><div><span className="kicker">REQUEST LEDGER</span><h2>命令确认</h2></div><span className="count">{status.commands.length}</span></div>
            {newestCommand ? <div className={`receipt receipt--${newestCommand.state}`}><div><span>#{newestCommand.request_id}</span><strong>{newestCommand.action}</strong></div><b>{labels[newestCommand.state]}</b></div> : <div className="empty-state">尚无命令。发送请求后将在此等待 ACK。</div>}
            <div className="log-list" aria-label="最新日志">{status.logs.slice(-4).reverse().map((entry, index) => <div className={`log log--${entry.level}`} key={`${entry.at_ns}-${index}`}><span>{entry.level}</span><p>{entry.message}</p></div>)}</div>
          </article>
        </section>
      </main>
      <footer><span>本地回环接口 · 不保存图像</span><span>安全状态：原型 / 需陪同测试</span></footer>
    </div>
  );
}
