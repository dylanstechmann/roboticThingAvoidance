'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
test('recovery v1 verifier passes', () => {
  const out = execFileSync(process.execPath, [path.join(root, 'tools/verify-recovery-v1.js')], {encoding: 'utf8'});
  assert.match(out, /Verified recovery v1: 64 cells x 20 runs/);
});
