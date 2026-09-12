import { calculateFrameBounds, drawEngine } from "./engine-renderer.js";

const element = (id) => document.getElementById(id);
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const state = {
  frames: [],
  bounds: {},
  maximumTemperature: 1,
  index: 0,
  playing: false,
  lastTick: 0,
  elapsed: 0,
  speed: 1,
};

function number(value, digits = 3) {
  return Number.isFinite(value) ? value.toFixed(digits) : "--";
}

function velocity(value) {
  if (Math.abs(value) < 0.0001) return "REST";
  return `${value > 0 ? "+" : ""}${number(value, 2)}c`;
}

function showReadouts(id, chamber) {
  const readings = [
    ["time", `t ${number(chamber.time)}`],
    ["chamber length", number(chamber.chamber_length)],
    ["piston length", number(chamber.piston_length)],
    ["face area", number(chamber.piston_face_area)],
    ["pressure", number(chamber.pressure)],
    ["volume", number(chamber.chamber_volume)],
    ["temperature", number(chamber.temperature)],
  ];
  element(id).innerHTML = readings
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");
}

function showMotion(id, chamber) {
  element(id).textContent =
    `piston ${velocity(chamber.piston_velocity)} / wall ${velocity(chamber.wall_velocity)}`;
}

function render() {
  const frame = state.frames[state.index];
  if (!frame) return;

  drawEngine(
    element("wall-canvas"),
    frame.wall,
    state.bounds.wall,
    frame.compression_fraction,
    state.maximumTemperature,
  );
  drawEngine(
    element("piston-canvas"),
    frame.piston,
    state.bounds.piston,
    frame.compression_fraction,
    state.maximumTemperature,
  );
  showReadouts("wall-readouts", frame.wall);
  showReadouts("piston-readouts", frame.piston);
  showMotion("wall-motion", frame.wall);
  showMotion("piston-motion", frame.piston);
  element("frame-number").textContent = `Frame ${state.index + 1}`;
  element("frame-total").textContent = state.frames.length;
  element("scrubber").value = state.index;
  element("compression").textContent =
    `Compression: ${number(frame.compression_fraction * 100, 1)}%`;
  element("current-time").textContent = `wall t = ${number(frame.wall.time)}`;
}

function setPlaying(playing) {
  state.playing = playing;
  element("play-pause").textContent = playing ? "Pause" : "Play";
  element("play-pause").setAttribute("aria-pressed", String(playing));
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
  element("play-pause").addEventListener("click", () => setPlaying(!state.playing));
  element("restart").addEventListener("click", () => {
    state.index = 0;
    state.elapsed = 0;
    render();
  });
  element("scrubber").addEventListener("input", (event) => {
    state.index = Number(event.target.value);
    state.elapsed = 0;
    render();
  });
  element("speed").addEventListener("change", (event) => {
    state.speed = Number(event.target.value);
  });
  window.addEventListener("resize", render);
}

async function fetchSimulation() {
  const baseUrl = import.meta.env?.BASE_URL ?? "./";
  const urls = [`${baseUrl}simulation.json`, `${baseUrl}public/simulation.json`];
  const failures = [];

  for (const url of urls) {
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (response.ok) return response.json();
      failures.push(`${url}: HTTP ${response.status}`);
    } catch (error) {
      failures.push(`${url}: ${error.message}`);
    }
  }
  throw new Error(failures.join("; "));
}

function prepareSimulation(data) {
  if (!Array.isArray(data.frames) || !data.frames.length) {
    throw new Error("The JSON file contains no animation frames");
  }
  state.frames = data.frames;
  state.bounds.wall = calculateFrameBounds(state.frames, "wall");
  state.bounds.piston = calculateFrameBounds(state.frames, "piston");
  state.maximumTemperature = Math.max(
    1,
    ...state.frames.flatMap((frame) => [frame.wall.temperature, frame.piston.temperature]),
  );
}

async function load() {
  try {
    const data = await fetchSimulation();
    prepareSimulation(data);
    element("particle-count").textContent =
      `${data.metadata?.particle_count ?? "--"} particles`;
    element("piston-speed").textContent =
      `piston ${number(Number(data.metadata?.piston_speed))}c`;
    element("formula").textContent =
      data.metadata?.temperature_formula || "T = P * V / (m * R)";
    element("scrubber").max = state.frames.length - 1;
    element("loading").hidden = true;
    element("viewer").hidden = false;
    bindControls();
    render();
    if (reducedMotion) {
      element("play-pause").setAttribute(
        "aria-label",
        "Play simulation (reduced motion enabled)",
      );
    }
  } catch (error) {
    console.error(error);
    element("loading").hidden = true;
    element("error-detail").textContent =
      window.location.protocol === "file:"
        ? "Browsers block local module data. Run `npm --prefix web run dev` and open the URL it prints."
        : `Could not load simulation data (${error.message}). Run the Python simulation first.`;
    element("error").hidden = false;
  }
}

load();
