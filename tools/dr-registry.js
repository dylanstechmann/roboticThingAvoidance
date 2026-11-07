#!/usr/bin/env node
'use strict';
// Computer-only DR registry: sim precedents are sealed; owner observations are append-only.
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '..');
const DEFAULT_SIM = path.join(ROOT, 'derived/dr-registry-v1/registry.json');
const DEFAULT_PHYSICAL = path.join(ROOT, 'derived/dr-registry-v1/physical-observations.json');
const BEHAVIORS = ['lateral_shift', 'replan_lanes', 'stall_stop', 'auto'];
const OUTCOMES = ['recovered', 'recovered_contact', 'blocked', 'stopped', 'incomplete'];
const CREDENTIAL = /sk-or-v1-|tgp_v1_|nvapi-|jina_[0-9a-z]|nck_live_|omtx_[0-9a-z]|s2k-|ghp_[A-Za-z0-9]|github_pat_/i;
const finite = v => typeof v === 'number' && Number.isFinite(v);
const nullableBool = v => v === null || typeof v === 'boolean';
function readJson(file) {
  const raw = fs.readFileSync(file, 'utf8');
  if (CREDENTIAL.test(raw)) throw new Error(`credential-like content in ${file}`);
  return JSON.parse(raw);
}
function segment(value) {
  if (!value || typeof value !== 'object' || typeof value.phase !== 'string' || !value.phase) throw new Error('route_segment.phase required');
  if (!['low', 'high'].includes(value.side)) throw new Error('route_segment.side must be low/high');
  if (!finite(value.x_center_in) || !Array.isArray(value.x_range_in) || value.x_range_in.length !== 2
      || !value.x_range_in.every(finite) || value.x_range_in[0] > value.x_range_in[1]) throw new Error('invalid route_segment x geometry');
}
function blocking(value) {
  if (!value || typeof value !== 'object' || typeof value.kind !== 'string' || !value.kind) throw new Error('blocking.kind required');
  if (!Array.isArray(value.footprint_in) || value.footprint_in.length !== 2 || !value.footprint_in.every(x => finite(x) && x > 0)) throw new Error('invalid blocking footprint');
  if (!finite(value.yaw_deg) || typeof value.spans_corridor !== 'boolean') throw new Error('invalid blocking yaw/span');
}
function validateEntry(entry, {physical = false} = {}) {
  if (!entry || typeof entry !== 'object' || entry.schema !== 'dr-registry-v1') throw new Error('dr-registry-v1 schema required');
  const kind = physical ? 'physical-observation' : 'sim';
  if (entry.entry_kind !== kind || typeof entry.entry_id !== 'string' || !entry.entry_id) throw new Error(`${kind} entry/id required`);
  if (typeof entry.world !== 'string' || !entry.world) throw new Error('world required');
  segment(entry.route_segment); blocking(entry.blocking);
  if (!OUTCOMES.concat(physical ? ['unknown'] : []).includes(entry.outcome)) throw new Error('invalid outcome');
  if (!nullableBool(entry.completion) || !nullableBool(entry.contact_free)) throw new Error('completion/contact_free must be boolean or null');
  if (!physical && (typeof entry.completion !== 'boolean' || typeof entry.contact_free !== 'boolean')) throw new Error('sim completion/contact_free must be boolean');
  if (entry.recovery_behavior !== null && !BEHAVIORS.includes(entry.recovery_behavior)) throw new Error('invalid recovery_behavior');
  if (physical) {
    if (entry.detection !== 'owner-observation' || entry.pose_mode !== null || entry.seed !== null || entry.source !== 'physical:owner') throw new Error('invalid physical fixed fields');
    if (typeof entry.observed_at !== 'string' || !Number.isFinite(Date.parse(entry.observed_at))) throw new Error('valid observed_at required');
    if (typeof entry.observed !== 'string' || !entry.observed.trim()) throw new Error('observed note required');
  } else {
    if (entry.detection !== 'truth' || !['true_pose', 'ekf_pose'].includes(entry.pose_mode)
        || !BEHAVIORS.includes(entry.recovery_behavior) || !Number.isInteger(entry.seed) || entry.source !== 'sim:evaluate-recovery-v1') throw new Error('invalid sim fixed fields');
    if (typeof entry.blocker_passed !== 'boolean' || !Number.isInteger(entry.blocker_contact_frames) || entry.blocker_contact_frames < 0
        || !finite(entry.time_s) || entry.time_s < 0 || !(entry.stop_reason === null || typeof entry.stop_reason === 'string')) throw new Error('invalid sim measurements');
    if (!(entry.blocker_pass_time_s === null || (finite(entry.blocker_pass_time_s) && entry.blocker_pass_time_s >= 0))) throw new Error('invalid blocker_pass_time_s');
    const passed = ['recovered', 'recovered_contact'].includes(entry.outcome);
    if (entry.blocker_passed !== passed || (passed && entry.blocker_pass_time_s === null) || (passed && entry.blocker_contact_frames !== 0)) throw new Error('inconsistent blocker outcome');
    if (entry.outcome === 'blocked' && (passed || entry.blocker_contact_frames === 0)) throw new Error('blocked outcome needs blocker contact');
  }
  return entry;
}
function loadEntries(file, options) {
  const rows = readJson(file);
  if (!Array.isArray(rows)) throw new Error(`${file} must contain an array`);
  const ids = new Set();
  for (const row of rows) {
    validateEntry(row, options);
    if (ids.has(row.entry_id)) throw new Error(`duplicate entry_id ${row.entry_id}`);
    ids.add(row.entry_id);
  }
  return rows;
}
function wilson(successes, n, z = 1.96) {
  if (!n) return null;
  const p = successes / n, d = 1 + z * z / n;
  const c = (p + z * z / (2 * n)) / d;
  const h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d;
  return [Number(Math.max(0, c - h).toFixed(4)), Number(Math.min(1, c + h).toFixed(4))];
}
function matches(entry, filters) {
  const r = entry.route_segment, b = entry.blocking;
  if (filters.side && r.side !== filters.side) return false;
  if (filters.kind && b.kind !== filters.kind) return false;
  if (filters.behavior && entry.recovery_behavior !== filters.behavior) return false;
  if (filters.x !== undefined && !(r.x_range_in[0] <= filters.x && filters.x <= r.x_range_in[1])) return false;
  return !filters.footprint || b.footprint_in.every((v, i) => Math.abs(v - filters.footprint[i]) <= 0.5);
}
function groups(rows) {
  return BEHAVIORS.filter(b => rows.some(r => r.recovery_behavior === b)).map(behavior => {
    const selected = rows.filter(r => r.recovery_behavior === behavior);
    const successes = selected.filter(r => ['recovered', 'recovered_contact'].includes(r.outcome)).length;
    return {recovery_behavior: behavior, matching_runs: selected.length, successes,
      success_rate: Number((successes / selected.length).toFixed(4)), wilson95: wilson(successes, selected.length),
      precedent_ids: selected.map(r => r.entry_id).sort()};
  });
}
function query(filters = {}, simPath = DEFAULT_SIM, physicalPath = DEFAULT_PHYSICAL) {
  if (filters.x !== undefined && !finite(filters.x)) throw new Error('x must be finite');
  if (filters.footprint && (!Array.isArray(filters.footprint) || filters.footprint.length !== 2 || !filters.footprint.every(finite))) throw new Error('footprint must be two numbers');
  const sim = loadEntries(simPath).filter(e => matches(e, filters));
  const physical = loadEntries(physicalPath, {physical: true}).filter(e => matches(e, filters));
  return {filters, groups: groups(sim), physical_observations: physical};
}
function stats(simPath = DEFAULT_SIM, physicalPath = DEFAULT_PHYSICAL) {
  const sim = loadEntries(simPath), physical = loadEntries(physicalPath, {physical: true});
  const outcomes = {};
  for (const e of [...sim, ...physical]) outcomes[e.outcome] = (outcomes[e.outcome] || 0) + 1;
  return {sim_entries: sim.length, physical_observations: physical.length, outcomes, behaviors: groups(sim)};
}
function addPhysical(input, physicalPath = DEFAULT_PHYSICAL) {
  const rows = loadEntries(physicalPath, {physical: true});
  const entry = {schema: 'dr-registry-v1', entry_kind: 'physical-observation', detection: 'owner-observation',
    pose_mode: null, recovery_behavior: null, outcome: 'unknown', completion: null, contact_free: null,
    seed: null, source: 'physical:owner', ...input};
  if (!entry.entry_id) {
    if (typeof entry.observed_at !== 'string' || !Number.isFinite(Date.parse(entry.observed_at))) throw new Error('valid observed_at required before ID assignment');
    const day = entry.observed_at.slice(0, 10).replaceAll('-', '');
    const prefix = `DR-phys-${day}-`;
    const used = rows.filter(r => r.entry_id.startsWith(prefix)).map(r => Number(r.entry_id.slice(prefix.length))).filter(Number.isInteger);
    entry.entry_id = `${prefix}${String((used.length ? Math.max(...used) : 0) + 1).padStart(2, '0')}`;
  }
  validateEntry(entry, {physical: true});
  if (rows.some(r => r.entry_id === entry.entry_id)) throw new Error(`duplicate entry_id ${entry.entry_id}`);
  rows.push(entry);
  const tmp = `${physicalPath}.tmp-${process.pid}`;
  fs.writeFileSync(tmp, JSON.stringify(rows, null, 2) + '\n', {flag: 'wx'});
  fs.renameSync(tmp, physicalPath);
  return entry;
}
function cli(argv) {
  const [command, ...rest] = argv;
  const flags = {};
  for (let i = 0; i < rest.length; i += 2) {
    if (!rest[i].startsWith('--') || rest[i + 1] === undefined) throw new Error('flags require values');
    flags[rest[i].slice(2)] = rest[i + 1];
  }
  const sim = flags.sim ? path.resolve(flags.sim) : DEFAULT_SIM;
  const physical = flags.physical ? path.resolve(flags.physical) : DEFAULT_PHYSICAL;
  if (command === 'query') {
    if (!flags.side || flags.x === undefined) throw new Error('query requires --side low|high --x INCHES');
    const filters = {side: flags.side, x: Number(flags.x)};
    if (flags.kind) filters.kind = flags.kind;
    if (flags.behavior) filters.behavior = flags.behavior;
    if (flags.footprint) filters.footprint = flags.footprint.split(',').map(Number);
    return query(filters, sim, physical);
  }
  if (command === 'stats') return stats(sim, physical);
  if (command === 'add-physical') {
    if (!flags.input) throw new Error('add-physical requires --input JSON');
    return addPhysical(readJson(path.resolve(flags.input)), physical);
  }
  throw new Error('usage: node tools/dr-registry.js query|add-physical|stats [flags]');
}
if (require.main === module) {
  try { console.log(JSON.stringify(cli(process.argv.slice(2)), null, 2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = {validateEntry, loadEntries, query, stats, addPhysical, groups, wilson};
