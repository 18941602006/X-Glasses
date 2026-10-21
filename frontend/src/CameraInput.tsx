import { useEffect, useRef, useState } from "react";

interface Props {
  enabled: boolean;
  busy: boolean;
  stopSignal: number;
  onFrame(image: string): Promise<boolean>;
  onActivity(active: boolean): void;
  onCancel(): void;
}

export function CameraInput({ enabled, busy, stopSignal, onFrame, onActivity, onCancel }: Props) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const permissionEpoch = useRef(0);
  const loopEpoch = useRef(0);
  const mounted = useRef(true);
  const [cameraOn, setCameraOn] = useState(false);
  const [opening, setOpening] = useState(false);
  const [looping, setLooping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stopLoop = () => {
    loopEpoch.current++;
    setLooping(false);
    onActivity(false);
  };
  const close = () => {
    permissionEpoch.current++;
    stopLoop();
    stream.current?.getTracks().forEach(track => track.stop());
    stream.current = null;
    if (video.current) video.current.srcObject = null;
    setCameraOn(false); setOpening(false);
    onCancel();
  };
  useEffect(() => { stopLoop(); }, [stopSignal]);
  useEffect(() => {
    mounted.current = true;
    const hidden = () => { if (document.hidden) close(); };
    document.addEventListener("visibilitychange", hidden);
    window.addEventListener("pagehide", close);
    return () => {
      mounted.current = false;
      permissionEpoch.current++; loopEpoch.current++;
      stream.current?.getTracks().forEach(track => track.stop());
      stream.current = null;
      document.removeEventListener("visibilitychange", hidden);
      window.removeEventListener("pagehide", close);
      onCancel();
    };
  }, []);

  const open = async () => {
    setError(null); setOpening(true);
    const epoch = ++permissionEpoch.current;
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("unsupported");
      const acquired = await navigator.mediaDevices.getUserMedia({
        audio: false, video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30, max: 30 } },
      });
      if (!mounted.current || epoch !== permissionEpoch.current) {
        acquired.getTracks().forEach(track => track.stop()); return;
      }
      stream.current = acquired;
      acquired.getVideoTracks().forEach(track => track.addEventListener("ended", close, { once: true }));
      if (!video.current) throw new Error("video_missing");
      video.current.srcObject = acquired;
      await video.current.play();
      if (!mounted.current || epoch !== permissionEpoch.current) return;
      setCameraOn(true);
    } catch (reason) {
      if (!mounted.current || epoch !== permissionEpoch.current) return;
      close();
      const name = reason && typeof reason === "object" && "name" in reason ? reason.name : "";
      setError(name === "NotAllowedError"
        ? "相机权限被拒绝：请允许此页面使用摄像头；内置浏览器不支持时请用本机 Chrome/Edge 打开同一链接"
        : "相机不可用：检查设备占用、系统权限；内置浏览器不支持时请用本机 Chrome/Edge 打开同一链接");
    } finally {
      if (mounted.current && epoch === permissionEpoch.current) setOpening(false);
    }
  };

  const capture = () => {
    const source = video.current;
    if (!source || source.videoWidth < 2 || source.videoHeight < 2 || document.hidden) {
      throw new Error("视频帧尚未就绪，请等待预览出现");
    }
    const scale = Math.min(640 / source.videoWidth, 480 / source.videoHeight, 1);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(source.videoWidth * scale);
    canvas.height = Math.round(source.videoHeight * scale);
    const context = canvas.getContext("2d");
    if (!context) throw new Error("浏览器无法抓取画面");
    context.drawImage(source, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.8);
  };
  const locate = async (continuous: boolean) => {
    setError(null);
    const epoch = ++loopEpoch.current;
    setLooping(continuous); onActivity(continuous);
    try {
      do {
        if (!stream.current || epoch !== loopEpoch.current) break;
        const succeeded = await onFrame(capture());
        if (!succeeded) break;
        if (continuous) await new Promise(resolve => setTimeout(resolve, 500));
      } while (continuous && mounted.current && epoch === loopEpoch.current);
    } catch (reason) {
      if (mounted.current && epoch === loopEpoch.current) setError(reason instanceof Error ? reason.message : "取帧定位失败");
    } finally {
      if (mounted.current && epoch === loopEpoch.current) stopLoop();
    }
  };

  return <div className="camera-input">
    <h3>本机实时视频</h3>
    <video ref={video} autoPlay muted playsInline hidden={!cameraOn} aria-label="本机摄像头实时预览" />
    {!cameraOn && <p>{opening ? "等待浏览器相机授权，可点击关闭取消" : "摄像头未开启"}</p>}
    <div className="camera-buttons">
      <button disabled={cameraOn || opening || busy} onClick={() => void open()}>开启摄像头</button>
      <button disabled={!cameraOn && !opening} onClick={close}>关闭摄像头</button>
      <button disabled={!cameraOn || busy || !enabled} onClick={() => void locate(false)}>取一帧找物</button>
      <button disabled={!cameraOn || busy || !enabled} onClick={() => void locate(true)}>开始连续找物</button>
      <button disabled={!looping} onClick={() => { stopLoop(); onCancel(); }}>停止连续找物</button>
    </div>
    <p className="control-note">视频只在本机预览，不录制、不传云。定位逐帧串行，完成后才取下一帧；它不是逐帧实时识别或安全避障。</p>
    {error && <p role="alert">{error}</p>}
  </div>;
}
