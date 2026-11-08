'use strict';
// Offline tests for the binary-STL inspector. Synthetic in-memory buffers
// exercise the parser and slice math; the archived spare tire pins the golden
// output agreed in GEOMETRY-AND-CONCEPTS.md (input sha256 e04ac6ac…,
// 5380 triangles, seven slice radii).

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { parseStl, sliceAtY, inspectStl } = require('../tools/inspect-tire-stl.js');

const root = path.resolve(__dirname, '..');

function binaryStl(triangles) {
  // Binary STL layout: 80-byte header, uint32 count, then 50 bytes per
  // triangle (12-byte normal + 9 float32 vertices + 2-byte attribute).
  const buffer = Buffer.alloc(84 + triangles.length * 50);
  buffer.writeUInt32LE(triangles.length, 80);
  triangles.forEach((tri, i) => {
    tri.forEach((v, j) => {
      for (let k = 0; k < 3; k++) buffer.writeFloatLE(v[k], 84 + i * 50 + 12 + j * 12 + k * 4);
    });
  });
  return buffer;
}

test('parseStl reads the triangle count and vertex bounds', () => {
  const { triangles, bounds } = parseStl(binaryStl([
    [[0, 0, 0], [1, 0, 0], [0, 2, 0]],
    [[2, 1, 3], [7, 1, 4], [2, 5, 4]]
  ]));
  assert.equal(triangles.length, 2);
  assert.deepEqual(bounds.min, [0, 0, 0]);
  assert.deepEqual(bounds.max, [7, 5, 4]);
});

test('parseStl rejects short and length-mismatched buffers', () => {
  assert.throws(() => parseStl(Buffer.alloc(10)), /Not a binary STL/);
  const valid = binaryStl([[[0, 0, 0], [1, 0, 0], [0, 1, 0]]]);
  assert.throws(() => parseStl(valid.subarray(0, valid.length - 1)), /Unexpected binary STL length/);
});

test('sliceAtY finds plane crossings of a known triangle', () => {
  // Vertical edge (1,0,1)->(1,2,1) crosses y=1 at (1,1,1); edge B-C meets the
  // plane at C=(-1,1,1). Both crossings sit at radius sqrt(2) about (0,0).
  const tri = [[1, 0, 1], [1, 2, 1], [-1, 1, 1]];
  const sample = sliceAtY([tri], 1, [0, 0]);
  assert.equal(sample.intersections, 2);
  assert.ok(Math.abs(sample.minSampledRadius - Math.SQRT2) < 1e-9);
  assert.ok(Math.abs(sample.maxSampledRadius - Math.SQRT2) < 1e-9);
});

test('sliceAtY reports nothing below a mesh', () => {
  const tri = [[0, 3, 0], [0, 4, 0], [1, 3, 0]];
  const sample = sliceAtY([tri], 0, [0, 0]);
  assert.equal(sample.intersections, 0);
  assert.equal(sample.minSampledRadius, null);
  assert.equal(sample.maxSampledRadius, null);
});

test('the archived spare tire matches the pinned geometry reference', () => {
  const stlPath = path.join(root, 'derived', 'organizer-cad', 'Spare Tire v2.stl');
  const report = inspectStl(fs.readFileSync(stlPath));
  // Pinned in GEOMETRY-AND-CONCEPTS.md (rounded to three decimals there).
  assert.equal(report.sha256, 'e04ac6ac4874902f0aa7a4383f738e04d0f0b0b88f553b85f008d66de448e2df');
  assert.equal(report.triangles, 5380);
  const expectedMin = [20.141, 20.136, 20.130, 20.127, 20.131, 20.137, 21.671];
  const expectedMax = [32.738, 34.108, 34.108, 34.108, 34.108, 34.080, 31.162];
  assert.equal(report.slices.length, 7);
  report.slices.forEach((slice, i) => {
    assert.ok(Math.abs(slice.minSampledRadius - expectedMin[i]) < 0.001, `slice ${i} min ${slice.minSampledRadius}`);
    assert.ok(Math.abs(slice.maxSampledRadius - expectedMax[i]) < 0.001, `slice ${i} max ${slice.maxSampledRadius}`);
  });
});