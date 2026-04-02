const BASE_URL = "/api";   // Vite proxy forwards to http://localhost:5000

export async function processFrame(frame, instruction, name, timestamp) {
  const res = await fetch(`${BASE_URL}/process-frame`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ frame, instruction, name, timestamp }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function resetStudent(name) {
  await fetch(`${BASE_URL}/reset/${encodeURIComponent(name)}`, {
    method: "POST",
  });
}