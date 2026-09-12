const colors = {
  background: "#0b1115",
  block: "#1a252c",
  blockEdge: "#52616a",
  piston: "#c7d2d8",
  pistonHighlight: "#eef4f6",
  pistonEdge: "#7ee0c1",
  wall: "#ffb38f",
  forward: "#7ee0c1",
  backward: "#ff8d68",
  text: "#8995a0",
};

export function calculateFrameBounds(frames, frameName) {
  const coordinates = frames.flatMap((frame) => {
    const chamber = frame[frameName];
    return [
      chamber.piston_position - chamber.piston_length,
      chamber.wall_position,
    ];
  });
  const minimum = Math.min(...coordinates);
  const maximum = Math.max(...coordinates);
  const padding = (maximum - minimum) * 0.025;
  return { minimum: minimum - padding, maximum: maximum + padding };
}

export function drawEngine(
  canvas,
  chamber,
  bounds,
  compressionFraction,
  maximumTemperature,
) {
  const rectangle = canvas.getBoundingClientRect();
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(rectangle.width * pixelRatio));
  canvas.height = Math.max(1, Math.round(rectangle.height * pixelRatio));

  const context = canvas.getContext("2d");
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  const width = rectangle.width;
  const height = rectangle.height;
  const engineLeft = 88;
  const engineRight = width - 25;
  const cylinderTop = 68;
  const cylinderBottom = height - 55;
  const cylinderMiddle = (cylinderTop + cylinderBottom) / 2;
  const pistonX = coordinateToCanvas(
    chamber.piston_position,
    bounds,
    engineLeft,
    engineRight,
  );
  const pistonBackX = coordinateToCanvas(
    chamber.piston_position - chamber.piston_length,
    bounds,
    engineLeft,
    engineRight,
  );
  const wallX = coordinateToCanvas(
    chamber.wall_position,
    bounds,
    engineLeft,
    engineRight,
  );

  context.clearRect(0, 0, width, height);
  context.fillStyle = colors.background;
  context.fillRect(0, 0, width, height);

  drawCoordinateGrid(context, engineLeft, engineRight, cylinderTop, cylinderBottom);
  drawEngineBlock(context, engineLeft, engineRight, cylinderTop, cylinderBottom);
  drawGas(
    context,
    pistonX,
    wallX,
    cylinderTop,
    cylinderBottom,
    chamber.model_temperature,
    maximumTemperature,
  );
  drawConnectingRod(context, pistonBackX, cylinderMiddle);
  drawPiston(context, pistonBackX, pistonX, cylinderTop, cylinderBottom);
  drawEndWall(context, wallX, cylinderTop, cylinderBottom);
  drawParticles(
    context,
    chamber,
    bounds,
    engineLeft,
    engineRight,
    cylinderTop,
    cylinderBottom,
  );
  drawVelocityIndicator(
    context,
    pistonX,
    cylinderTop - 32,
    chamber.piston_velocity,
    "PISTON",
  );
  drawVelocityIndicator(
    context,
    wallX,
    cylinderTop - 14,
    chamber.wall_velocity,
    "WALL",
  );
  drawCompressionLabel(
    context,
    pistonX,
    wallX,
    cylinderBottom,
    compressionFraction,
  );
}

function coordinateToCanvas(position, bounds, left, right) {
  const coordinateSpan = bounds.maximum - bounds.minimum || 1;
  const fraction = (position - bounds.minimum) / coordinateSpan;
  return left + fraction * (right - left);
}

function drawCoordinateGrid(context, left, right, top, bottom) {
  context.strokeStyle = "rgba(126, 224, 193, 0.07)";
  context.lineWidth = 1;
  for (let index = 0; index <= 10; index += 1) {
    const x = left + ((right - left) * index) / 10;
    context.beginPath();
    context.moveTo(x, top - 18);
    context.lineTo(x, bottom + 18);
    context.stroke();
  }
}

function drawEngineBlock(context, left, right, top, bottom) {
  context.fillStyle = colors.block;
  context.fillRect(left - 14, top - 17, right - left + 28, 17);
  context.fillRect(left - 14, bottom, right - left + 28, 17);
  context.strokeStyle = colors.blockEdge;
  context.lineWidth = 2;
  context.strokeRect(left, top, right - left, bottom - top);

  context.fillStyle = "#718089";
  for (let x = left - 4; x <= right + 4; x += 52) {
    context.beginPath();
    context.arc(x, top - 9, 2.2, 0, Math.PI * 2);
    context.arc(x, bottom + 9, 2.2, 0, Math.PI * 2);
    context.fill();
  }
}

function drawGas(context, pistonX, wallX, top, bottom, temperature, maximum) {
  const heat = Math.min(1, Math.max(0, temperature / maximum));
  const red = Math.round(40 + heat * 215);
  const green = Math.round(126 - heat * 35);
  const blue = Math.round(137 - heat * 82);
  const gasLeft = Math.min(pistonX, wallX);
  const gasWidth = Math.abs(wallX - pistonX);
  const gradient = context.createLinearGradient(gasLeft, top, gasLeft + gasWidth, bottom);
  gradient.addColorStop(0, `rgba(${red}, ${green}, ${blue}, 0.18)`);
  gradient.addColorStop(1, `rgba(${red}, ${green}, ${blue}, 0.42)`);
  context.fillStyle = gradient;
  context.fillRect(gasLeft, top + 4, gasWidth, bottom - top - 8);
}

function drawConnectingRod(context, pistonBackX, middle) {
  const wristPinX = pistonBackX + 10;
  context.lineCap = "round";
  context.strokeStyle = "#0b1013";
  context.lineWidth = 17;
  context.beginPath();
  context.moveTo(12, middle);
  context.lineTo(wristPinX, middle);
  context.stroke();
  context.strokeStyle = "#718089";
  context.lineWidth = 7;
  context.stroke();
  context.lineCap = "butt";

  context.fillStyle = "#11191e";
  context.strokeStyle = "#aab6bc";
  context.lineWidth = 3;
  context.beginPath();
  context.arc(23, middle, 17, 0, Math.PI * 2);
  context.fill();
  context.stroke();
}

function drawPiston(context, pistonBackX, pistonX, top, bottom) {
  const bodyLeft = Math.min(pistonBackX, pistonX);
  const bodyWidth = Math.max(8, Math.abs(pistonX - pistonBackX));
  const bodyHeight = bottom - top - 12;
  const gradient = context.createLinearGradient(bodyLeft, top, pistonX, bottom);
  gradient.addColorStop(0, colors.pistonHighlight);
  gradient.addColorStop(0.45, colors.piston);
  gradient.addColorStop(1, "#87959d");
  context.fillStyle = gradient;
  context.strokeStyle = colors.pistonEdge;
  context.lineWidth = 2;
  context.fillRect(bodyLeft, top + 6, bodyWidth, bodyHeight);
  context.strokeRect(bodyLeft, top + 6, bodyWidth, bodyHeight);

  context.fillStyle = "#3b4951";
  for (let offset = 5; offset <= 11; offset += 3) {
    context.fillRect(pistonX - offset, top + 7, 1.5, bodyHeight - 2);
  }

  context.fillStyle = "#263138";
  context.strokeStyle = "#dfe8ec";
  context.beginPath();
  context.arc(bodyLeft + bodyWidth * 0.38, (top + bottom) / 2, 8, 0, Math.PI * 2);
  context.fill();
  context.stroke();
}

function drawEndWall(context, wallX, top, bottom) {
  context.fillStyle = colors.wall;
  context.fillRect(wallX - 5, top - 4, 10, bottom - top + 8);
  context.fillStyle = "rgba(255, 179, 143, 0.25)";
  for (let y = top - 2; y < bottom; y += 12) {
    context.fillRect(wallX + 5, y, 14, 5);
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
    context.globalAlpha = 0.3;
    context.lineWidth = 1.4;
    context.beginPath();
    context.moveTo(x - velocity * 13, y);
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

function drawVelocityIndicator(context, x, y, velocity, label) {
  const speed = Number(velocity) || 0;
  context.font = "9px ui-monospace, monospace";
  context.textAlign = "center";
  context.fillStyle = colors.text;
  if (Math.abs(speed) < 0.0001) {
    context.fillText(`${label} REST`, x, y);
    return;
  }

  const direction = Math.sign(speed);
  const arrowLength = 28 * direction;
  context.strokeStyle = direction > 0 ? colors.forward : colors.backward;
  context.fillStyle = context.strokeStyle;
  context.lineWidth = 1.5;
  context.beginPath();
  context.moveTo(x - arrowLength / 2, y + 4);
  context.lineTo(x + arrowLength / 2, y + 4);
  context.lineTo(x + arrowLength / 2 - 5 * direction, y);
  context.moveTo(x + arrowLength / 2, y + 4);
  context.lineTo(x + arrowLength / 2 - 5 * direction, y + 8);
  context.stroke();
  context.fillText(`${label} ${speed > 0 ? "+" : ""}${speed.toFixed(2)}c`, x, y - 3);
}

function drawCompressionLabel(context, pistonX, wallX, bottom, compressionFraction) {
  context.fillStyle = colors.text;
  context.font = "10px ui-monospace, monospace";
  context.textAlign = "center";
  context.fillText(
    `${(compressionFraction * 100).toFixed(1)}% COMPRESSION`,
    (pistonX + wallX) / 2,
    bottom + 35,
  );
  context.textAlign = "start";
}
