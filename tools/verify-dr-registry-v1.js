#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const registry = require('./dr-registry.js');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'derived/dr-registry-v1');
const simPath = path.join(dir, 'registry.json');
const physicalPath = path.join(dir, 'physical-observations.json');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
assert.equal(manifest.access, 'computer-only');
assert.equal(manifest.sim_entry_count, 1280);
assert.equal(sha(fs.readFileSync(simPath)), manifest.registry_sha256);
assert.match(manifest.note, /no read or write path/);
const rows = registry.loadEntries(simPath);
assert.equal(rows.length, 1280);
const scenarios = ['low_mid', 'low_corner', 'high_mid', 'high_corner', 'low_mid_band', 'low_corner_band', 'high_mid_band', 'high_corner_band'];
const behaviors = ['lateral_shift', 'replan_lanes', 'stall_stop', 'auto'];
const expected = [];
for (const scenario of scenarios) for (const behavior of behaviors) for (const pose of ['true_pose', 'ekf_pose']) {
  for (let seed = 100; seed < 120; seed++) expected.push(`DR-sim-${scenario}-${behavior}-${pose}-${seed}`);
}
assert.deepEqual(rows.map(r => r.entry_id).sort(), expected.sort());
registry.loadEntries(physicalPath, {physical: true});  // may be empty, but every owner entry must validate

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dr-registry-v1-'));
try {
  const physical = path.join(tmp, 'physical.json');
  fs.writeFileSync(physical, '[]\n');
  const result = registry.query({side: 'low', x: 60, kind: 'guide-plush', behavior: 'auto'}, simPath, physical);
  assert.equal(result.groups.length, 1);
  assert.equal(result.groups[0].recovery_behavior, 'auto');
  assert.equal(result.groups[0].matching_runs, 160);
  assert.equal(result.groups[0].precedent_ids.length, 160);
  assert.equal(result.physical_observations.length, 0);
  const sample = {
    world: 'world-ccw-line-sq-adv-align', observed_at: '2026-11-07T12:00:00Z',
    route_segment: {phase: 'lap', side: 'low', x_center_in: 60, x_range_in: [44, 80]},
    blocking: {kind: 'guide-plush', footprint_in: [8.55, 8.2], yaw_deg: 0, spans_corridor: true},
    recovery_behavior: 'auto', observed: 'SYNTHETIC verifier fixture; not a physical trial'
  };
  const input = path.join(tmp, 'observation.json');
  fs.writeFileSync(input, JSON.stringify(sample));
  const tool = path.join(root, 'tools/dr-registry.js');
  const added = JSON.parse(execFileSync(process.execPath, [tool, 'add-physical', '--input', input, '--physical', physical], {encoding: 'utf8'}));
  assert.equal(added.entry_id, 'DR-phys-20261107-01');
  assert.equal(added.outcome, 'unknown');
  assert.throws(() => registry.addPhysical({...sample, entry_id: added.entry_id}, physical), /duplicate entry_id/);
  assert.throws(() => registry.addPhysical({world: sample.world}, physical), /observed_at|route_segment|blocking/);
  const stats = JSON.parse(execFileSync(process.execPath, [tool, 'stats', '--sim', simPath, '--physical', physical], {encoding: 'utf8'}));
  assert.equal(stats.sim_entries, 1280); assert.equal(stats.physical_observations, 1);
  const queried = registry.query({side: 'low', x: 60, behavior: 'auto'}, simPath, physical);
  assert.equal(queried.physical_observations.length, 1);
  assert.equal(queried.physical_observations[0].observed, sample.observed);
  assert.equal(registry.loadEntries(physical, {physical: true}).length, 1);
  assert.equal(sha(fs.readFileSync(simPath)), manifest.registry_sha256, 'CLI cannot modify sim registry');
} finally {
  fs.rmSync(tmp, {recursive: true, force: true});
}
console.log('Verified DR registry v1: 1280 unique sim entries, complete coverage, host-only query/add/stats on temporary observations.');
