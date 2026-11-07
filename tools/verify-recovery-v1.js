#!/usr/bin/env node
'use strict';
// Verifies recovery-v1 structure and hashes; results are checked as measured, not for a desired direction.
// Regenerate: uv run --no-project --python 3.12 python -B -I tools/evaluate-recovery-v1.py
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'derived/recovery-v1');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
for (const [f, h] of Object.entries(manifest.input_hashes)) assert.equal(sha(fs.readFileSync(path.join(root, f))), h, `stale input ${f}`);
for (const [f, h] of Object.entries(manifest.output_hashes)) assert.equal(sha(fs.readFileSync(path.join(dir, f))), h, `output ${f} changed`);
const report = JSON.parse(fs.readFileSync(path.join(dir, 'report.json'), 'utf8'));
assert.deepEqual(report.seeds, Array.from({length: 20}, (_, i) => 100 + i));
const scenarios = ['low_mid', 'low_corner', 'high_mid', 'high_corner', 'low_mid_band', 'low_corner_band', 'high_mid_band', 'high_corner_band'];
const behaviors = ['lateral_shift', 'replan_lanes', 'stall_stop', 'auto'];
const poses = ['true_pose', 'ekf_pose'];
assert.equal(report.cells.length, 64);
const keys = new Set();
const bounded01 = (v, name) => assert.ok(Number.isFinite(v) && v >= 0 && v <= 1, `${name} in [0,1]`);
const interval = (v, name) => {
  assert.ok(Array.isArray(v) && v.length === 2, `${name} interval`);
  bounded01(v[0], name); bounded01(v[1], name); assert.ok(v[0] <= v[1], `${name} ordered`);
};
for (const scenario of scenarios) for (const behavior of behaviors) for (const pose of poses) {
  const key = `${scenario}|${behavior}|${pose}`;
  const c = report.cells.find(x => x.scenario === scenario && x.behavior === behavior && x.pose_mode === pose);
  assert.ok(c, `missing ${key}`); keys.add(key);
  assert.equal(c.runs, 20);
  for (const k of ['completed', 'passed_blocker', 'recovered', 'recovered_contact', 'blocked', 'stopped', 'incomplete']) {
    assert.ok(Number.isInteger(c[k]) && c[k] >= 0 && c[k] <= 20, `${key} ${k}`);
  }
  assert.equal(c.recovered + c.recovered_contact + c.blocked + c.stopped + c.incomplete, 20, `${key} outcomes`);
  assert.equal(c.passed_blocker, c.recovered + c.recovered_contact, `${key} passed`);
  interval(c.passed_wilson95, `${key} Wilson`);
  assert.ok(Number.isFinite(c.mean_time_s) && c.mean_time_s >= 0);
}
assert.equal(keys.size, 64);
const a = report.association;
assert.equal(a.units, 320); assert.equal(a.independent_clusters, 40); assert.equal(a.scenario_rows_per_cluster, 8);
assert.equal(a.permutation_shuffles, 10000); assert.equal(a.permutation_seed, 7);
assert.match(a.method, /midrank Spearman/); assert.match(a.method, /clusters within pose/);
assert.match(a.router_pass_definition, /planned_contact_vehicles == 0/); assert.match(a.router_pass_definition, /not baseline completion/);
for (const prefix of ['recovery_success_vs_router_pass', 'recovery_success_vs_planned_contacts']) {
  const rho = a[`${prefix}_spearman`], p = a[`${prefix}_p`];
  assert.ok(rho === null || (Number.isFinite(rho) && rho >= -1 && rho <= 1));
  assert.ok(p === null || (Number.isFinite(p) && p >= 0 && p <= 1));
  assert.equal(rho === null, p === null, `${prefix}: null statistic and p-value agree`);
}
for (const k of ['recovery_success_among_router_pass_rows', 'recovery_success_among_router_fail_rows']) {
  assert.ok(a[k] === null || (Number.isFinite(a[k]) && a[k] >= 0 && a[k] <= 1));
}
assert.match(a.note, /not 320 independent observations/);
for (const pose of poses) {
  const b = report.baseline.pose_modes[pose];
  assert.equal(b.runs, 20);
  for (const k of ['completed', 'router_passes']) assert.ok(Number.isInteger(b[k]) && b[k] >= 0 && b[k] <= 20);
  interval(b.completion_wilson95, `${pose} completion`); interval(b.router_pass_wilson95, `${pose} router`);
  assert.ok(Number.isFinite(b.mean_planned_contacts) && b.mean_planned_contacts >= 0);
}
const summary = fs.readFileSync(path.join(dir, 'summary.md'), 'utf8');
for (const text of ['midrank Spearman', '40 independent', 'directional crossing', 'backtrack', 'pit_bypass', 'sensed-detection']) assert.ok(summary.includes(text), `summary documents ${text}`);
console.log('Verified recovery v1: 64 cells x 20 runs, 40 clustered baselines, midrank association and honest limitations.');
