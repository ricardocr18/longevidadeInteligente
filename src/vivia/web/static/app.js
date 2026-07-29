const micBtn = document.getElementById("mic-btn");
const statusText = document.getElementById("status-text");
const transcript = document.getElementById("transcript");
const player = document.getElementById("player");
const textForm = document.getElementById("text-form");
const textInput = document.getElementById("text-input");
const personaSelect = document.getElementById("persona-select");
const momentSelect = document.getElementById("moment-select");
const momentField = document.getElementById("moment-field");
const settingsToggle = document.getElementById("settings-toggle");
const settingsPanel = document.getElementById("settings-panel");
const restartBtn = document.getElementById("restart-btn");

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let testMode = false;
let sessionStarted = false;
let recordingStartedAt = 0;

// Duração mínima de gravação — abaixo disso, é bem provável que o
// áudio esteja vazio/silencioso, o que faz o modelo de transcrição
// "alucinar" texto aleatório (às vezes em outro idioma) em vez de
// simplesmente retornar vazio.
const MIN_RECORDING_MS = 700;

// Escolhe o melhor codec suportado pelo navegador, em vez de deixar o
// MediaRecorder decidir sozinho — evita que o servidor receba um
// container que a API de transcrição interpreta mal.
function pickMimeType() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/mp4",
  ];
  for (const type of candidates) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return ""; // deixa o navegador decidir, último recurso
}

function extensionFor(mimeType) {
  if (mimeType.includes("webm")) return "webm";
  if (mimeType.includes("ogg")) return "ogg";
  if (mimeType.includes("mp4")) return "m4a";
  return "webm";
}

// ── Estados visuais da orb ──────────────────────────────────────────
function setOrbState(state) {
  micBtn.classList.remove("idle", "listening", "thinking", "speaking");
  micBtn.classList.add(state);
}

const STATUS_LABELS = {
  idle: "Toque para falar com a Vivia",
  listening: "Ouvindo… toque de novo para parar",
  thinking: "Vivia está pensando…",
  speaking: "Vivia está falando…",
};

function setStatus(state, customText) {
  setOrbState(state);
  statusText.textContent = customText || STATUS_LABELS[state] || "";
}

// ── Transcript ───────────────────────────────────────────────────────
function addBubble(who, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${who}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = who === "vivia" ? "Vivia" : "Você";
  const body = document.createElement("span");
  body.textContent = text;
  bubble.appendChild(label);
  bubble.appendChild(body);
  transcript.appendChild(bubble);
  bubble.scrollIntoView({ behavior: "smooth", block: "end" });
  return bubble;
}

// Player de conferência: toca de volta exatamente o que foi gravado,
// antes/junto do envio — ajuda a diagnosticar na hora se a captura
// pegou a voz de verdade ou só silêncio.
function addRecordingPreview(blob) {
  const wrap = document.createElement("div");
  wrap.className = "bubble user recording-preview";
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = "Sua gravação (conferir)";
  const audioEl = document.createElement("audio");
  audioEl.controls = true;
  audioEl.src = URL.createObjectURL(blob);
  wrap.appendChild(label);
  wrap.appendChild(audioEl);
  transcript.appendChild(wrap);
  wrap.scrollIntoView({ behavior: "smooth", block: "end" });
}

// ── Configuração inicial (personas / momentos / modo de teste) ─────
async function loadConfig() {
  const res = await fetch("/api/config");
  const cfg = await res.json();
  testMode = cfg.test_mode;

  personaSelect.innerHTML = "";
  cfg.personas.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.nome;
    personaSelect.appendChild(opt);
  });

  if (testMode) {
    momentField.hidden = false;
    momentSelect.innerHTML = "";
    cfg.moments.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.label;
      momentSelect.appendChild(opt);
    });
  }
}

function currentPersona() {
  return personaSelect.value;
}

function currentMoment() {
  return testMode ? momentSelect.value : "";
}

// ── Reprodução de áudio (base64 -> player) ──────────────────────────
function playAudioBase64(b64) {
  return new Promise((resolve) => {
    player.src = `data:audio/mpeg;base64,${b64}`;
    setStatus("speaking");
    player.onended = () => {
      setStatus("idle");
      resolve();
    };
    player.play().catch(() => {
      setStatus("idle");
      resolve();
    });
  });
}

// ── Chamadas à API ───────────────────────────────────────────────────
async function startSession() {
  setStatus("thinking");
  const form = new FormData();
  form.append("user_id", currentPersona());
  if (testMode && currentMoment()) form.append("moment", currentMoment());

  const res = await fetch("/api/start", { method: "POST", body: form });
  const data = await res.json();

  addBubble("vivia", data.text);
  await playAudioBase64(data.audio_base64);
  sessionStarted = true;
}

async function sendText(text) {
  addBubble("user", text);
  setStatus("thinking");

  const form = new FormData();
  form.append("user_id", currentPersona());
  form.append("text", text);
  if (testMode && currentMoment()) form.append("moment", currentMoment());

  const res = await fetch("/api/message", { method: "POST", body: form });
  const data = await res.json();

  addBubble("vivia", data.text);
  await playAudioBase64(data.audio_base64);
}

async function sendAudio(blob, mimeType) {
  setStatus("thinking");

  const ext = extensionFor(mimeType);
  const form = new FormData();
  form.append("user_id", currentPersona());
  if (testMode && currentMoment()) form.append("moment", currentMoment());
  form.append("audio", blob, `gravacao.${ext}`);

  const res = await fetch("/api/voice-message", { method: "POST", body: form });
  const data = await res.json();

  addBubble("user", data.transcript);
  addBubble("vivia", data.text);
  await playAudioBase64(data.audio_base64);
}

// ── Gravação de áudio ────────────────────────────────────────────────
async function toggleRecording() {
  if (!sessionStarted) {
    await startSession();
    return;
  }

  if (isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = pickMimeType();
    mediaRecorder = mimeType
      ? new MediaRecorder(stream, { mimeType })
      : new MediaRecorder(stream);

    audioChunks = [];
    recordingStartedAt = Date.now();

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());

      const durationMs = Date.now() - recordingStartedAt;
      const usedMimeType = mediaRecorder.mimeType || mimeType || "audio/webm";
      const blob = new Blob(audioChunks, { type: usedMimeType });

      console.log(
        `[Vivia] gravação: ${durationMs}ms, ${blob.size} bytes, tipo: ${usedMimeType}`
      );

      if (durationMs < MIN_RECORDING_MS || blob.size < 1000) {
        setStatus(
          "idle",
          "Gravação muito curta — toque e fale por pelo menos 1-2 segundos."
        );
        return;
      }

      addRecordingPreview(blob);
      await sendAudio(blob, usedMimeType);
    };

    mediaRecorder.start();
    isRecording = true;
    setStatus("listening");
  } catch (err) {
    statusText.textContent =
      "Não consegui acessar o microfone. Você pode digitar sua mensagem abaixo.";
  }
}

// ── Eventos ──────────────────────────────────────────────────────────
micBtn.addEventListener("click", toggleRecording);

textForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = textInput.value.trim();
  if (!text) return;
  textInput.value = "";
  if (!sessionStarted) await startSession();
  await sendText(text);
});

settingsToggle.addEventListener("click", () => {
  const isHidden = settingsPanel.hidden;
  settingsPanel.hidden = !isHidden;
  settingsToggle.setAttribute("aria-expanded", String(isHidden));
});

restartBtn.addEventListener("click", async () => {
  restartBtn.disabled = true;
  restartBtn.textContent = "Reiniciando…";
  try {
    const form = new FormData();
    form.append("user_id", currentPersona());
    await fetch("/api/reset", { method: "POST", body: form });
  } catch (err) {
    console.warn("[Vivia] falha ao limpar histórico no servidor:", err);
  }
  transcript.innerHTML = "";
  sessionStarted = false;
  setStatus("idle");
  restartBtn.disabled = false;
  restartBtn.textContent = "Reiniciar conversa";
});

personaSelect.addEventListener("change", () => {
  transcript.innerHTML = "";
  sessionStarted = false;
  setStatus("idle");
});

// ── Inicialização ────────────────────────────────────────────────────
setOrbState("idle");
loadConfig();