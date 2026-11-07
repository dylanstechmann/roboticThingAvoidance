'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
test('DR registry v1 verifier and temporary-file CLI checks pass', () => {
  const out = execFileSync(process.execPath, [path.join(root, 'tools/verify-dr-registry-v1.js')], {encoding: 'utf8'});
  assert.match(out, /Verified DR registry v1: 1280 unique sim entries/);
});
