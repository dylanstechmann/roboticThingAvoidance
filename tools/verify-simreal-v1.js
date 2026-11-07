#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'derived/simreal-v1');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const gitShow = (commit, file) => execFileSync('git', ['-c', `safe.directory=${root}`, 'show', `${commit}:${file}`], {cwd: root, stdio: ['ignore', 'pipe', 'ignore']});
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
for (const [f, h] of Object.entries(manifest.input_hashes)) assert.equal(sha(fs.readFileSync(path.join(root, f))), h, `stale input ${f}`);
for (const [f, h] of Object.entries(manifest.output_hashes)) assert.equal(sha(fs.readFileSync(path.join(dir, f))), h, `output ${f} changed`);
const report = JSON.parse(fs.readFileSync(path.join(dir, 'report.json'), 'utf8'));
const samples = JSON.parse(fs.readFileSync(path.join(dir, 'drift-samples.json'), 'utf8'));
assert.equal(manifest.source_commits.length, 6);
assert.equal(new Set(manifest.source_commits.map(s => s.world)).size, 6);
const sources = new Map();
for (const source of manifest.source_commits) {
  assert.match(source.source_commit, /^[0-9a-f]{40}$/);
  const prefix = `derived/rl-v3/${source.world}`;
  const reportBytes = gitShow(source.source_commit, `${prefix}/report.json`);
  const manifestBytes = gitShow(source.source_commit, `${prefix}/manifest.json`);
  assert.equal(sha(reportBytes), source.source_report_sha256);
  assert.equal(sha(manifestBytes), source.source_manifest_sha256);
  const sourceManifest = JSON.parse(manifestBytes);
  for (const [f, h] of Object.entries(sourceManifest.input_hashes)) assert.equal(sha(gitShow(source.source_commit, f)), h, `${source.world}: stale ${f}`);
  assert.equal(sha(reportBytes), sourceManifest.output_hashes['report.json']);
  assert.equal(sha(gitShow(source.source_commit, `${prefix}/summary.md`)), sourceManifest.output_hashes['summary.md']);
  sources.set(source.world, JSON.parse(reportBytes));
}
assert.equal(report.records.length, 18);
assert.equal(new Set(report.records.map(r => `${r.world}|${r.policy}`)).size, 18);
const ordered = (o, name, unitInterval = false) => {
  assert.ok(o.p2_5 <= o.p50 && o.p50 <= o.p97_5, `${name} ordered`);
  if (unitInterval) for (const v of Object.values(o)) assert.ok(Number.isFinite(v) && v >= 0 && v <= 1, `${name} range`);
};
for (const r of report.records) {
  const source = sources.get(r.world);
  assert.ok(source, `source for ${r.world}`);
  const cell = source.results.find(c => c.policy === r.policy);
  assert.ok(cell, `${r.world}/${r.policy}`);
  assert.equal(r.sim_completed, cell.completed); assert.equal(r.sim_runs, cell.runs);
  assert.equal(r.sim_pass_rate, Number((cell.completed / cell.runs).toFixed(4)));
  const sourceSeal = manifest.source_commits.find(s => s.world === r.world);
  assert.equal(r.source_commit, sourceSeal.source_commit); assert.equal(r.source_report_sha256, sourceSeal.source_report_sha256);
  assert.equal(r.n_draws, 10000); assert.ok(Number.isInteger(r.draw_seed));
  assert.equal(r.corridor_width_in, 22.5); assert.deepEqual(r.tolerances, {drift_mm: 25, spin_deg: 5});
  ordered(r.expected_physical_pass, 'expected', true); ordered(r.drift_mm_1m, 'drift'); ordered(r.spin_error_deg_360, 'spin');
  assert.equal(r.fragile, r.sim_pass_rate >= 0.8 && r.expected_physical_pass.p2_5 < 0.5);
  assert.equal(r.drift_source, samples.source); assert.equal(r.provisional, samples.provisional);
  assert.equal(r.e03_sample_counts.straight, samples.drift_mm.length);
  assert.equal(r.e03_sample_counts.spin, samples.spin_error_deg.length);
  assert.ok(Array.isArray(r.sim_pass_wilson95) && r.sim_pass_wilson95.length === 2);
}
if (samples.provisional) {
  assert.equal(samples.source, 'provisional-plant');
  assert.equal(samples.parameters.support_configurations_modeled, false);
  assert.match(samples.basis.drift, /synthetic, not tape/); assert.match(samples.basis.spin, /synthetic, not tape/);
} else {
  assert.match(samples.source, /^e03:/);
  assert.ok(manifest.input_hashes[samples.provenance.path]);
}
assert.equal(report.model.limitation, 'not a full-mission physical-pass probability');
const summary = fs.readFileSync(path.join(dir, 'summary.md'), 'utf8');
assert.match(summary, /not a full-mission physical-pass probability/);
assert.match(summary, /not a validated error distribution/);
if (samples.provisional) assert.match(summary, /near-zero lateral drift is a model limitation/);
console.log(`Verified simreal v1: 18 records across six immutable world seals; ${samples.provisional ? 'provisional synthetic' : 'measured E03'} transfer inputs.`);
