#!/usr/bin/env node
'use strict';
// Intersect binary STL triangles with planes normal to Y; coordinates remain in STL units.
// Refactored so the parser and slice math are directly testable; CLI output is unchanged.
const fs = require('node:fs');
const crypto = require('node:crypto');

function parseStl(buffer) {
  if (buffer.length < 84) throw new Error('Not a binary STL');
  const count = buffer.readUInt32LE(80);
  if (buffer.length !== 84 + count * 50) throw new Error('Unexpected binary STL length');
  const triangles = [], lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < count; i++) {
    const tri = [];
    for (let j = 0; j < 3; j++) {
      const v = [0, 1, 2].map(k => buffer.readFloatLE(84 + i * 50 + 12 + j * 12 + k * 4));
      if (!v.every(Number.isFinite)) throw new Error('Non-finite vertex');
      v.forEach((n, k) => { lo[k] = Math.min(lo[k], n); hi[k] = Math.max(hi[k], n); });
      tri.push(v);
    }
    triangles.push(tri);
  }
  return { triangles, bounds: { min: lo, max: hi } };
}

function sliceAtY(triangles, y, center) {
  const radii = [];
  for (const t of triangles) for (let i = 0; i < 3; i++) {
    const a = t[i], b = t[(i + 1) % 3];
    if ((a[1] <= y && b[1] > y) || (b[1] <= y && a[1] > y)) {
      const f = (y - a[1]) / (b[1] - a[1]);
      radii.push(Math.hypot(a[0] + f * (b[0] - a[0]) - center[0], a[2] + f * (b[2] - a[2]) - center[1]));
    }
  }
  return { y, intersections: radii.length, minSampledRadius: radii.length ? Math.min(...radii) : null, maxSampledRadius: radii.length ? Math.max(...radii) : null };
}

function inspectStl(buffer) {
  const { triangles, bounds } = parseStl(buffer);
  const lo = bounds.min, hi = bounds.max;
  const extent = hi.map((x, i) => x - lo[i]);
  const center = [(lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2];
  return {
    sha256: crypto.createHash('sha256').update(buffer).digest('hex'),
    triangles: triangles.length,
    units: 'unspecified by STL',
    min: lo, max: hi, extent, centerXZFromBounds: center,
    slices: [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99].map(f => sliceAtY(triangles, lo[1] + extent[1] * f, center)),
    caveat: 'Intersection vertices are samples; neither true minimum radial clearance between vertices nor topology or manufactured dimensions are certified.'
  };
}

function main() {
  const target = process.argv[2];
  if (!target) { console.error('Usage: node inspect-tire-stl.js binary.stl'); process.exit(1); }
  const data = fs.readFileSync(target);
  console.log(JSON.stringify(inspectStl(data), null, 2));
}

if (require.main === module) {
  main();
}

module.exports = { parseStl, sliceAtY, inspectStl };