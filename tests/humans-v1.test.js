'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
test('humans v1 verifier passes', () => {
  const out = execFileSync(process.execPath, [path.join(root, 'tools/verify-humans-v1.js')], {encoding: 'utf8'});
  assert.match(out, /Verified humans v1: 10 cells x 20 runs/);
});
