#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'derived/humans-v1');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
for (const [f, h] of Object.entries(manifest.input_hashes)) assert.equal(sha(fs.readFileSync(path.join(root, f))), h, `stale input ${f}`);
for (const [f, h] of Object.entries(manifest.output_hashes)) assert.equal(sha(fs.readFileSync(path.join(dir, f))), h, `output ${f} changed`);
const report = JSON.parse(fs.readFileSync(path.join(dir, 'report.json'), 'utf8'));
assert.deepEqual(report.seeds, Array.from({length: 20}, (_, i) => 100 + i));
assert.equal(report.cells.length, 10);
assert.equal(report.model.human_radius_in, 5);
assert.equal(report.model.abort, 'first human contact');
assert.deepEqual(report.model.nested_zone_order, ['start', 'pit_lane', 'lane_change', 'turn']);
assert.match(report.model.trend_caveat, /confounded/);
assert.match(report.model.corridor_geometry, /wall-adjacent/);
const interval = (v, name) => {
  assert.ok(Array.isArray(v) && v.length === 2, `${name} interval`);
  assert.ok(v[0] >= 0 && v[0] <= v[1] && v[1] <= 1, `${name} bounds`);
};
const quantile = (values, q) => {
  const v = [...values].sort((a, b) => a - b), pos = (v.length - 1) * q;
  const lo = Math.floor(pos), hi = Math.ceil(pos);
  return v[lo] * (1 - (pos - lo)) + v[hi] * (pos - lo);
};
let totalRuns = 0;
const placementsBySeed = new Map();
for (let n = 1; n <= 10; n++) {
  const c = report.cells.find(x => x.n_humans === n);
  assert.ok(c, `missing N=${n}`); assert.equal(c.runs, 20); assert.equal(c.runs_detail.length, 20);
  totalRuns += c.runs;
  assert.deepEqual(c.runs_detail.map(r => r.seed), report.seeds);
  for (const r of c.runs_detail) {
    assert.equal(typeof r.completed, 'boolean'); assert.equal(typeof r.aborted, 'boolean');
    assert.ok(Number.isInteger(r.human_contact_count) && r.human_contact_count >= 0 && r.human_contact_count <= n);
    assert.ok(Number.isInteger(r.human_contact_frames) && r.human_contact_frames >= 0);
    assert.ok(Number.isFinite(r.min_clearance_in)); assert.ok(Number.isFinite(r.time_s) && r.time_s >= 0);
    assert.match(r.human_set_id, /^[0-9a-f]{64}$/);
    if (!placementsBySeed.has(r.seed)) placementsBySeed.set(r.seed, new Set());
    placementsBySeed.get(r.seed).add(r.human_set_id);
    if (r.aborted) {
      assert.ok(r.human_contact_count > 0, 'abort requires human contact');
      assert.equal(r.stop_reason, 'human_contact'); assert.ok(r.human_contact_frames >= 1);
    }
    if (r.human_contact_count > 0) assert.ok(r.aborted, 'first contact aborts immediately');
    if (r.completed) { assert.ok(!r.aborted); assert.equal(r.state, 'DONE'); }
  }
  const completed = c.runs_detail.filter(r => r.completed).length;
  const contacts = c.runs_detail.filter(r => r.human_contact_count > 0).length;
  const aborted = c.runs_detail.filter(r => r.aborted).length;
  assert.equal(c.completed, completed); assert.equal(c.human_contact_runs, contacts); assert.equal(c.aborted, aborted);
  assert.equal(c.human_contact_count, c.runs_detail.reduce((s, r) => s + r.human_contact_count, 0));
  assert.equal(c.completion_rate, Number((completed / 20).toFixed(4)));
  assert.equal(c.human_contact_rate, Number((contacts / 20).toFixed(4)));
  assert.equal(c.aborted_rate, Number((aborted / 20).toFixed(4)));
  interval(c.completion_wilson95, `N=${n} completion`); interval(c.human_contact_wilson95, `N=${n} contact`);
  interval(c.aborted_wilson95, `N=${n} abort`);
  const clearances = c.runs_detail.map(r => r.min_clearance_in);
  assert.equal(c.min_clearance_in.p50, Number(quantile(clearances, 0.5).toFixed(4)));
  assert.equal(c.min_clearance_in.p05, Number(quantile(clearances, 0.05).toFixed(4)));
  assert.ok(c.min_clearance_in.p05 <= c.min_clearance_in.p50);
}
assert.equal(totalRuns, 200);
assert.equal(placementsBySeed.size, 20);
const uniquePlacementSets = new Set();
for (const [seed, ids] of placementsBySeed) {
  assert.equal(ids.size, 1, `seed ${seed} shares one nested placement set across N`);
  uniquePlacementSets.add([...ids][0]);
}
assert.equal(uniquePlacementSets.size, 20, 'each seed has a distinct placement set; no cross-seed reuse');
const summary = fs.readFileSync(path.join(dir, 'summary.md'), 'utf8');
for (const text of ['no causal or monotonic trend', 'not human perception', 'wall-adjacent bands', 'not a physical safety qualification']) assert.ok(summary.includes(text), `summary documents ${text}`);
console.log('Verified humans v1: 10 cells x 20 runs (200), immediate human-contact aborts, clearance percentiles and limitations.');
