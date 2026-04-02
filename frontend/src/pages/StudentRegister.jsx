import { useState, useRef, useCallback } from "react";
import CameraFeed from "../components/CameraFeed";
import { processFrame } from "../services/api";

const INSTRUCTIONS = [
  { text: "Look straight at the camera", yaw: 0 },
  { text: "Turn your face slightly left",  yaw: -15 },
  { text: "Turn your face slightly right", yaw: 15 },
  { text: "Move closer to the camera",     size: "near" },
  { text: "Move farther from the camera",  size: "far" },
];

const MAX_FRAMES = 10;

const STATUS_MSG = {
  no_face:         "No face detected — look at the camera",
  no_landmarks:    "Can't read face — adjust lighting",
  invalid_face:    "Face too small or out of frame",
  adjust_pose:     "Adjust your head position",
  adjust_distance: "Adjust your distance from camera",
  captured:        "✓ Frame captured!",
  step_completed:  "✓ Step complete!",
};

export default function StudentRegister() {
  const [name,      setName]      = useState("");
  const [started,   setStarted]   = useState(false);
  const [step,      setStep]      = useState(0);
  const [count,     setCount]     = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [done,      setDone]      = useState(false);
  const [capturing, setCapturing] = useState(false);

  const sessionStart  = useRef(Date.now());
  const processingRef = useRef(false);  // blocks overlapping requests

  const handleFrame = useCallback(async (frame) => {
    if (processingRef.current || done || !started) return;
    processingRef.current = true;

    const instruction = INSTRUCTIONS[step];
    const timestamp   = Date.now() - sessionStart.current;

    try {
      const result = await processFrame(frame, instruction, name, timestamp);

      if (result.status === "captured") {
        setCount(result.count);
        setStatusMsg(`✓ ${result.count} / ${MAX_FRAMES}`);

      } else if (result.status === "step_completed") {
        setStatusMsg("✓ Step complete!");
        setCount(0);

        const next = step + 1;
        if (next >= INSTRUCTIONS.length) {
          setDone(true);
          setCapturing(false);
        } else {
          setStep(next);
        }
      } else {
        setStatusMsg(STATUS_MSG[result.status] ?? result.status);
      }
    } catch {
      setStatusMsg("⚠ Connection error — is the backend running?");
    } finally {
      processingRef.current = false;
    }
  }, [step, name, done, started]);

  const handleStart = () => {
    if (!name.trim()) return;
    sessionStart.current = Date.now();
    setStarted(true);
    setCapturing(true);
    setStep(0);
    setCount(0);
    setDone(false);
    setStatusMsg("");
  };

  const handleReset = () => {
    setStarted(false);
    setDone(false);
    setName("");
    setStep(0);
    setCount(0);
    setStatusMsg("");
    setCapturing(false);
  };

  const progress    = Math.round((count / MAX_FRAMES) * 100);
  const instruction = INSTRUCTIONS[step];

  return (
    <div style={s.page}>
      <div style={s.card}>
        <h1 style={s.title}>Student Face Registration</h1>

        {/* ── Name input ── */}
        {!started && (
          <div style={s.row}>
            <input
              style={s.input}
              type="text"
              placeholder="Enter your full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleStart()}
            />
            <button
              style={{ ...s.btn, opacity: name.trim() ? 1 : 0.4 }}
              disabled={!name.trim()}
              onClick={handleStart}
            >
              Start
            </button>
          </div>
        )}

        {/* ── Active capture ── */}
        {started && !done && (
          <>
            {/* Step dots */}
            <div style={s.dots}>
              {INSTRUCTIONS.map((_, i) => (
                <div key={i} style={{
                  ...s.dot,
                  background: i < step ? "#22c55e" : i === step ? "#3b82f6" : "#334155",
                }} />
              ))}
            </div>

            {/* Instruction banner */}
            <div style={s.banner}>
              <span style={s.stepLabel}>Step {step + 1} / {INSTRUCTIONS.length}</span>
              <span style={s.instrText}>{instruction.text}</span>
            </div>

            {/* Camera + overlay */}
            <div style={s.camWrap}>
              <CameraFeed onFrame={handleFrame} active={capturing} interval={800} />
              {statusMsg && <div style={s.overlay}>{statusMsg}</div>}
            </div>

            {/* Progress bar */}
            <div style={s.track}>
              <div style={{ ...s.fill, width: `${progress}%` }} />
            </div>
            <p style={s.countText}>{count} / {MAX_FRAMES} frames captured</p>
          </>
        )}

        {/* ── Done screen ── */}
        {done && (
          <div style={s.doneBox}>
            <div style={s.doneIcon}>✓</div>
            <h2 style={s.doneTitle}>Registration Complete!</h2>
            <p style={s.doneSub}>
              Face data for <strong>{name}</strong> has been saved.
            </p>
            <button style={s.btn} onClick={handleReset}>
              Register Another Student
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const s = {
  page:      { minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center", background:"linear-gradient(135deg,#0f172a,#1e293b)", fontFamily:"'Segoe UI',system-ui,sans-serif", padding:"24px" },
  card:      { background:"#1e293b", border:"1px solid #334155", borderRadius:"20px", padding:"40px 36px", width:"100%", maxWidth:"480px", color:"#f1f5f9", boxShadow:"0 25px 60px rgba(0,0,0,.5)" },
  title:     { fontSize:"1.5rem", fontWeight:700, marginBottom:"28px", textAlign:"center" },
  row:       { display:"flex", gap:"10px", marginBottom:"20px" },
  input:     { flex:1, padding:"10px 14px", borderRadius:"10px", border:"1px solid #475569", background:"#0f172a", color:"#f1f5f9", fontSize:"0.95rem", outline:"none" },
  btn:       { padding:"10px 20px", borderRadius:"10px", border:"none", background:"#3b82f6", color:"#fff", fontWeight:600, cursor:"pointer", fontSize:"0.95rem" },
  dots:      { display:"flex", gap:"8px", justifyContent:"center", marginBottom:"20px" },
  dot:       { width:"12px", height:"12px", borderRadius:"50%", transition:"background 0.3s" },
  banner:    { background:"#0f172a", borderRadius:"12px", padding:"14px 20px", marginBottom:"18px", display:"flex", flexDirection:"column", gap:"4px" },
  stepLabel: { fontSize:"0.75rem", color:"#64748b", textTransform:"uppercase", letterSpacing:"0.05em" },
  instrText: { fontSize:"1.05rem", fontWeight:600, color:"#e2e8f0" },
  camWrap:   { position:"relative", textAlign:"center", marginBottom:"16px" },
  overlay:   { position:"absolute", bottom:"12px", left:"50%", transform:"translateX(-50%)", background:"rgba(0,0,0,.7)", color:"#fff", padding:"6px 16px", borderRadius:"20px", fontSize:"0.85rem", whiteSpace:"nowrap", pointerEvents:"none" },
  track:     { height:"6px", borderRadius:"999px", background:"#334155", overflow:"hidden", marginBottom:"8px" },
  fill:      { height:"100%", background:"linear-gradient(90deg,#3b82f6,#22c55e)", borderRadius:"999px", transition:"width 0.3s ease" },
  countText: { textAlign:"center", fontSize:"0.82rem", color:"#94a3b8", margin:0 },
  doneBox:   { textAlign:"center", padding:"20px 0" },
  doneIcon:  { fontSize:"3rem", color:"#22c55e", marginBottom:"12px" },
  doneTitle: { fontSize:"1.4rem", fontWeight:700, marginBottom:"8px" },
  doneSub:   { color:"#94a3b8", marginBottom:"24px", fontSize:"0.9rem" },
};