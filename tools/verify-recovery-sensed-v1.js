#!/usr/bin/env node
'use strict';
// Verifies recovery-sensed-v1 structure and hashes; results are checked as measured, not for a
// desired direction. Regenerate: uv run --no-project --python 3.12 python -B -I tools/evaluate-recovery-sensed-v1.py
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'derived/recovery-sensed-v1');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
assert.equal(manifest.smoke, false, 'the sealed package must be the full (20-seed) run, not a smoke run');
for (const [f, h] of Object.entries(manifest.input_hashes)) assert.equal(sha(fs.readFileSync(path.join(root, f))), h, `stale input ${f}`);
for (const [f, h] of Object.entries(manifest.output_hashes)) assert.equal(sha(fs.readFileSync(path.join(dir, f))), h, `output ${f} changed`);
const report = JSON.parse(fs.readFileSync(path.join(dir, 'report.json'), 'utf8'));
assert.deepEqual(report.seeds, Array.from({length: 20}, (_, i) => 100 + i));
const scenarios = ['low_mid', 'low_corner', 'high_mid', 'high_corner', 'low_mid_band', 'low_corner_band', 'high_mid_band', 'high_corner_band'];
const behaviors = ['lateral_shift', 'replan_lanes', 'stall_stop', 'auto'];
const poses = ['true_pose', 'ekf_pose'];
const bounded01 = (v, name) => assert.ok(Number.isFinite(v) && v >= 0 && v <= 1, `${name} in [0,1]`);
const interval = (v, name) => {
  assert.ok(Array.isArray(v) && v.length === 2, `${name} interval`);
  bounded01(v[0], name); bounded01(v[1], name); assert.ok(v[0] <= v[1], `${name} ordered`);
};
const keys = new Set();
for (const scenario of scenarios) for (const behavior of behaviors) for (const pose of poses) {
  const key = `${scenario}|${behavior}|${pose}`;
  const c = report.cells.find(x => x.scenario === scenario && x.behavior === behavior && x.pose_mode === pose);
  assert.ok(c, `missing ${key}`); keys.add(key);
  assert.equal(c.runs, 20);
  for (const k of ['completed', 'passed_blocker', 'recovered', 'recovered_contact', 'blocked', 'stopped', 'incomplete', 'contact_before_confirm']) {
    assert.ok(Number.isInteger(c[k]) && c[k] >= 0 && c[k] <= 20, `${key} ${k}`);
  }
  assert.equal(c.recovered + c.recovered_contact + c.blocked + c.stopped + c.incomplete, 20, `${key} outcomes`);
  assert.equal(c.passed_blocker, c.recovered + c.recovered_contact, `${key} passed`);
  interval(c.passed_wilson95, `${key} Wilson`);
  assert.ok(Number.isFinite(c.mean_time_s) && c.mean_time_s >= 0, `${key} mean_time_s`);
  bounded01(c.confirmed_rate, `${key} confirmed_rate`);
  assert.ok(Number.isFinite(c.mean_replans) && c.mean_replans >= 0, `${key} mean_replans`);
}
assert.equal(keys.size, 64);
const rows = JSON.parse(fs.readFileSync(path.join(dir, 'rows.json'), 'utf8'));
assert.equal(rows.length, 1280, '1280 sensed rows');
for (const r of rows) {
  assert.equal(r.detection, 'sensed', r.entry_id);
  assert.equal(r.schema, 'recovery-sensed-v1', r.entry_id);
  assert.match(r.entry_id, /^RS-sim-[a-z_]+-(lateral_shift|replan_lanes|stall_stop|auto)-(true_pose|ekf_pose)-\d+$/);
  assert.ok(['never', 'before_contact', 'after_contact'].includes(r.confirm_status), `${r.entry_id} confirm_status`);
  assert.ok(Number.isInteger(r.replan_count) && r.replan_count >= 0, `${r.entry_id} replan_count`);
  assert.ok(Number.isInteger(r.sensed_vehicles) && r.sensed_vehicles >= 0, `${r.entry_id} sensed_vehicles`);
  assert.ok(['recovered', 'recovered_contact', 'blocked', 'stopped', 'incomplete'].includes(r.outcome), `${r.entry_id} outcome`);
}
assert.equal(report.baseline.length, 40, '40 unblocked sensed baselines');
for (const b of report.baseline) {
  assert.ok(poses.includes(b.pose_mode), 'baseline pose_mode');
  assert.ok(Number.isInteger(b.seed) && b.seed >= 100 && b.seed <= 119, 'baseline seed');
  assert.equal(typeof b.completed, 'boolean', 'baseline completed');
  assert.ok(Number.isInteger(b.planned_contact_vehicles) && b.planned_contact_vehicles >= 0, 'baseline planned contacts');
}
assert.equal(report.comparison.length, 64, '64 oracle-vs-sensed comparisons');
const seen = new Set();
for (const c of report.comparison) {
  const k = `${c.scenario}|${c.behavior}|${c.pose_mode}`;
  assert.ok(!seen.has(k), `duplicate comparison ${k}`); seen.add(k);
  bounded01(c.oracle_recovered_rate, `${k} oracle`);
  bounded01(c.sensed_recovered_rate, `${k} sensed`);
}
console.log(`Verified recovery sensed v1: 64 cells x 20 runs, ${rows.length} sensed rows, 40 baselines, 64 comparisons`);