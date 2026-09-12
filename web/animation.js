(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { frames: [], index: 0, playing: false, lastTick: 0, elapsed: 0, speed: 1 };
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const colors = { ink: "#e8edf2", muted: "#8995a0", line: "#34434c", accent: "#7ee0c1" };

  function number(value, digits = 3) {
    return Number.isFinite(value) ? value.toFixed(digits) : "--";
  }

  function showReadouts(id, chamber) {
    $(id).innerHTML = [
      ["time", `t ${number(chamber.time, 3)}`],
      ["pressure", `${number(chamber.pressure, 3)} P`],
      ["volume", `${number(chamber.chamber_volume, 3)} V`],
      ["temperature", number(chamber.temperature, 3)]
    ].map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`).join("");
  }

  function draw(canvas, chamber) {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const width = rect.width;
    const height = rect.height;
    ctx.clearRect(0, 0, width, height);
    const left = 25, right = width - 25, top = 29, bottom = height - 29;
    const piston = Number(chamber.piston_position);
    const wall = Number(chamber.wall_position);
    const lowerBound = Math.min(piston, wall);
    const span = Math.abs(wall - piston) || 1;

    ctx.strokeStyle = colors.line;
    ctx.lineWidth = 1;
    ctx.strokeRect(left, top, right - left, bottom - top);
    ctx.strokeStyle = colors.accent;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(left, top - 1); ctx.lineTo(left, bottom + 1);
    ctx.moveTo(right, top - 1); ctx.lineTo(right, bottom + 1);
    ctx.stroke();
    ctx.fillStyle = colors.muted;
    ctx.font = "10px ui-monospace, monospace";
    ctx.fillText(`x ${number(piston, 2)}`, left - 9, bottom + 18);
    ctx.fillText(`x ${number(wall, 2)}`, right - 26, bottom + 18);

    const positions = Array.isArray(chamber.particle_positions) ? chamber.particle_positions : [];
    const velocities = Array.isArray(chamber.particle_velocities) ? chamber.particle_velocities : [];
    const maxVelocity = Math.max(1, ...velocities.map((v) => Math.abs(Number(v))));
    positions.forEach((position, index) => {
      const fraction = Math.max(0, Math.min(1, (Number(position) - lowerBound) / span));
      const x = left + fraction * (right - left);
      const y = top + 14 + ((index * 47) % Math.max(24, bottom - top - 28));
      const velocity = Number(velocities[index]) || 0;
      const intensity = Math.min(1, Math.abs(velocity) / maxVelocity);
      const hue = velocity >= 0 ? 164 : 16;
      ctx.fillStyle = `hsl(${hue} ${55 + intensity * 25}% ${48 + intensity * 18}%)`;
      ctx.beginPath(); ctx.arc(x, y, 2.4 + intensity * 1.8, 0, Math.PI * 2); ctx.fill();
    });
  }

  function render() {
    const frame = state.frames[state.index];
    if (!frame) return;
    draw($("wall-canvas"), frame.wall);
    draw($("piston-canvas"), frame.piston);
    showReadouts("wall-readouts", frame.wall);
    showReadouts("piston-readouts", frame.piston);
    $("frame-number").textContent = `Frame ${state.index + 1}`;
    $("frame-total").textContent = state.frames.length;
    $("scrubber").value = state.index;
    $("compression").textContent = `Compression: ${number(Number(frame.compression_fraction) * 100, 1)}%`;
    $("current-time").textContent = `t = ${number(frame.wall.time, 3)}`;
  }

  function setPlaying(playing) {
    state.playing = playing;
    $("play-pause").textContent = playing ? "Pause" : "Play";
    $("play-pause").setAttribute("aria-pressed", String(playing));
    state.lastTick = performance.now();
    if (playing) requestAnimationFrame(tick);
  }

  function tick(now) {
    if (!state.playing) return;
    const interval = 1000 / (30 * state.speed);
    state.elapsed += now - state.lastTick;
    state.lastTick = now;
    while (state.elapsed >= interval) {
      state.elapsed -= interval;
      state.index = (state.index + 1) % state.frames.length;
    }
    render();
    requestAnimationFrame(tick);
  }

  function bindControls() {
    $("play-pause").addEventListener("click", () => setPlaying(!state.playing));
    $("restart").addEventListener("click", () => { state.index = 0; state.elapsed = 0; render(); });
    $("scrubber").addEventListener("input", (event) => { state.index = Number(event.target.value); state.elapsed = 0; render(); });
    $("speed").addEventListener("change", (event) => { state.speed = Number(event.target.value); });
    window.addEventListener("resize", render);
  }

  async function load() {
    try {
      const simulationUrl = `${import.meta.env.BASE_URL}simulation.json`;
      const response = await fetch(simulationUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.frames) || !data.frames.length) throw new Error("No frames");
      state.frames = data.frames;
      $("particle-count").textContent = `${data.metadata?.particle_count ?? "--"} particles`;
      $("piston-speed").textContent = `piston ${number(Number(data.metadata?.piston_speed), 3)}c`;
      $("formula").textContent = data.metadata?.temperature_formula || "T = P * V / (m * R)";
      $("scrubber").max = state.frames.length - 1;
      $("loading").hidden = true;
      $("viewer").hidden = false;
      bindControls();
      render();
      if (reducedMotion) $("play-pause").setAttribute("aria-label", "Play simulation (reduced motion enabled)");
    } catch (error) {
      console.error(error);
      $("loading").hidden = true;
      $("error").hidden = false;
    }
  }

  load();
})();
