'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
test('recovery sensed v1 verifier passes', () => {
  const out = execFileSync(process.execPath, [path.join(root, 'tools/verify-recovery-sensed-v1.js')], {encoding: 'utf8'});
  assert.match(out, /Verified recovery sensed v1: 64 cells x 20 runs, 1280 sensed rows, 40 baselines, 64 comparisons/);
});