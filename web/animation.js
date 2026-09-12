(() => {
  "use strict";

  const element = (id) => document.getElementById(id);
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const colors = {
    background: "#0b1115",
    block: "#1a252c",
    blockEdge: "#52616a",
    gasCold: "rgba(46, 133, 140, 0.18)",
    gasHot: "rgba(255, 112, 72, 0.42)",
    piston: "#d7e0e5",
    pistonEdge: "#7ee0c1",
    wall: "#ffb38f",
    forward: "#7ee0c1",
    backward: "#ff8d68",
    text: "#8995a0",
  };
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

  function showReadouts(id, chamber) {
    element(id).innerHTML = [
      ["time", `t ${number(chamber.time)}`],
      ["pressure", number(chamber.pressure)],
      ["volume", number(chamber.chamber_volume)],
      ["temperature", number(chamber.temperature)],
    ]
      .map(
        ([label, value]) =>
          `<div><dt>${label}</dt><dd>${value}</dd></div>`,
      )
      .join("");
  }

  function calculateBounds(frameName) {
    const coordinates = state.frames.flatMap((frame) => {
      const chamber = frame[frameName];
      return [chamber.piston_position, chamber.wall_position];
    });
    return {
      minimum: Math.min(...coordinates),
      maximum: Math.max(...coordinates),
    };
  }

  function coordinateToCanvas(position, bounds, left, right) {
    const coordinateSpan = bounds.maximum - bounds.minimum || 1;
    const fraction = (position - bounds.minimum) / coordinateSpan;
    return left + fraction * (right - left);
  }

  function gasColor(temperature) {
    const heat = Math.min(1, Math.max(0, temperature / state.maximumTemperature));
    return heat < 0.25 ? colors.gasCold : colors.gasHot;
  }

  function drawEngine(canvas, chamber, bounds, compressionFraction) {
    const rectangle = canvas.getBoundingClientRect();
    const pixelRatio = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(rectangle.width * pixelRatio));
    canvas.height = Math.max(1, Math.round(rectangle.height * pixelRatio));

    const context = canvas.getContext("2d");
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    const width = rectangle.width;
    const height = rectangle.height;
    const cylinderLeft = Math.max(76, width * 0.16);
    const cylinderRight = width - 30;
    const cylinderTop = 54;
    const cylinderBottom = height - 54;
    const cylinderMiddle = (cylinderTop + cylinderBottom) / 2;
    const pistonX = coordinateToCanvas(
      chamber.piston_position,
      bounds,
      cylinderLeft,
      cylinderRight,
    );
    const wallX = coordinateToCanvas(
      chamber.wall_position,
      bounds,
      cylinderLeft,
      cylinderRight,
    );
    const gasLeft = Math.min(pistonX, wallX);
    const gasRight = Math.max(pistonX, wallX);

    context.clearRect(0, 0, width, height);
    context.fillStyle = colors.background;
    context.fillRect(0, 0, width, height);

    drawCylinder(context, cylinderLeft, cylinderRight, cylinderTop, cylinderBottom);

    context.fillStyle = gasColor(chamber.temperature);
    context.fillRect(
      gasLeft,
      cylinderTop + 5,
      gasRight - gasLeft,
      cylinderBottom - cylinderTop - 10,
    );

    drawActuatorRod(context, pistonX, cylinderMiddle);
    drawPiston(context, pistonX, cylinderTop, cylinderBottom);
    drawEndWall(context, wallX, cylinderTop, cylinderBottom);
    drawParticles(context, chamber, bounds, cylinderLeft, cylinderRight, cylinderTop, cylinderBottom);
    drawLabels(context, pistonX, wallX, cylinderTop, cylinderBottom, compressionFraction);
  }

  function drawCylinder(context, left, right, top, bottom) {
    context.fillStyle = colors.block;
    context.fillRect(left - 8, top - 11, right - left + 16, 11);
    context.fillRect(left - 8, bottom, right - left + 16, 11);
    context.strokeStyle = colors.blockEdge;
    context.lineWidth = 1.5;
    context.strokeRect(left, top, right - left, bottom - top);

    context.strokeStyle = "rgba(126, 224, 193, 0.12)";
    context.setLineDash([4, 8]);
    context.beginPath();
    context.moveTo(left, (top + bottom) / 2);
    context.lineTo(right, (top + bottom) / 2);
    context.stroke();
    context.setLineDash([]);
  }

  function drawActuatorRod(context, pistonX, middle) {
    const rodEnd = Math.max(14, pistonX - 7);
    context.lineCap = "round";
    context.strokeStyle = "#11191e";
    context.lineWidth = 13;
    context.beginPath();
    context.moveTo(12, middle);
    context.lineTo(rodEnd, middle);
    context.stroke();
    context.strokeStyle = "#75838b";
    context.lineWidth = 5;
    context.stroke();
    context.lineCap = "butt";
  }

  function drawPiston(context, pistonX, top, bottom) {
    context.fillStyle = colors.piston;
    context.strokeStyle = colors.pistonEdge;
    context.lineWidth = 2;
    context.fillRect(pistonX - 7, top + 2, 14, bottom - top - 4);
    context.strokeRect(pistonX - 7, top + 2, 14, bottom - top - 4);

    context.fillStyle = "#3b4951";
    context.fillRect(pistonX - 4, top + 13, 8, 3);
    context.fillRect(pistonX - 4, bottom - 16, 8, 3);
  }

  function drawEndWall(context, wallX, top, bottom) {
    context.fillStyle = colors.wall;
    context.fillRect(wallX - 4, top - 3, 8, bottom - top + 6);
    context.fillStyle = "rgba(255, 179, 143, 0.22)";
    for (let y = top; y < bottom; y += 13) {
      context.fillRect(wallX + 4, y, 10, 5);
    }
  }

  function drawParticles(context, chamber, bounds, left, right, top, bottom) {
    const positions = chamber.particle_positions ?? [];
    const velocities = chamber.particle_velocities ?? [];
    const verticalSpace = Math.max(24, bottom - top - 28);

    positions.forEach((position, index) => {
      const x = coordinateToCanvas(Number(position), bounds, left, right);
      const y = top + 14 + ((index * 47) % verticalSpace);
      const velocity = Number(velocities[index]) || 0;
      const particleColor = velocity >= 0 ? colors.forward : colors.backward;

      context.strokeStyle = particleColor;
      context.globalAlpha = 0.28;
      context.lineWidth = 1.4;
      context.beginPath();
      context.moveTo(x - velocity * 12, y);
      context.lineTo(x, y);
      context.stroke();

      context.globalAlpha = 0.9;
      context.fillStyle = particleColor;
      context.beginPath();
      context.arc(x, y, 2.4, 0, Math.PI * 2);
      context.fill();
      context.globalAlpha = 1;
    });
  }

  function drawLabels(context, pistonX, wallX, top, bottom, compressionFraction) {
    context.fillStyle = colors.text;
    context.font = "10px ui-monospace, monospace";
    context.textAlign = "center";
    context.fillText("PISTON", pistonX, top - 22);
    context.fillText("END WALL", wallX, top - 22);
    context.fillText(
      `${number(compressionFraction * 100, 1)}% COMPRESSION`,
      (pistonX + wallX) / 2,
      bottom + 31,
    );
    context.textAlign = "start";
  }

  function render() {
    const frame = state.frames[state.index];
    if (!frame) return;

    drawEngine(
      element("wall-canvas"),
      frame.wall,
      state.bounds.wall,
      frame.compression_fraction,
    );
    drawEngine(
      element("piston-canvas"),
      frame.piston,
      state.bounds.piston,
      frame.compression_fraction,
    );
    showReadouts("wall-readouts", frame.wall);
    showReadouts("piston-readouts", frame.piston);
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
    element("play-pause").addEventListener("click", () => {
      setPlaying(!state.playing);
    });
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

  async function load() {
    try {
      const data = await fetchSimulation();
      if (!Array.isArray(data.frames) || !data.frames.length) {
        throw new Error("The JSON file contains no animation frames");
      }
      state.frames = data.frames;
      state.bounds.wall = calculateBounds("wall");
      state.bounds.piston = calculateBounds("piston");
      state.maximumTemperature = Math.max(
        1,
        ...state.frames.flatMap((frame) => [
          frame.wall.temperature,
          frame.piston.temperature,
        ]),
      );

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
})();
