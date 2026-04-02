import { useEffect, useRef, useCallback } from "react";

export default function CameraFeed({ onFrame, active = true, interval = 800 }) {
  const videoRef  = useRef(null);
  const canvasRef = useRef(null);
  const timerRef  = useRef(null);

  // Start webcam
  useEffect(() => {
    let stream = null;
    navigator.mediaDevices
      .getUserMedia({ video: { width: 320, height: 240, facingMode: "user" } })
      .then((s) => {
        stream = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      })
      .catch((err) => console.error("Webcam error:", err));

    return () => {
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Capture one frame and send it up
  const capture = useCallback(() => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    const ctx = canvas.getContext("2d");
    // Mirror to match what the user sees
    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(video, -320, 0, 320, 240);
    ctx.restore();

    onFrame(canvas.toDataURL("image/jpeg", 0.8));
  }, [onFrame]);

  // Start/stop interval based on active prop
  useEffect(() => {
    if (active) {
      timerRef.current = setInterval(capture, interval);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [active, capture, interval]);

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <video
        ref={videoRef}
        autoPlay playsInline muted
        width={320} height={240}
        style={{ transform: "scaleX(-1)", borderRadius: "12px", display: "block" }}
      />
      <canvas ref={canvasRef} width={320} height={240} style={{ display: "none" }} />
    </div>
  );
}