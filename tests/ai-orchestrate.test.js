'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  sha256,
  containsCredential,
  loadProviderRegistry,
  loadTaskManifest,
  loadSecretsFile,
  selectProvider,
  buildPrompt,
  runTask,
  parseArgs,
  DEFAULT_REGISTRY,
  DEFAULT_MANIFEST,
  DEFAULT_SECRETS_FILE
} = require('../tools/ai-orchestrate.js');

const root = path.resolve(__dirname, '..');

test('sha256 is stable', () => {
  assert.equal(sha256('abc'), sha256('abc'));
  assert.match(sha256('abc'), /^[0-9a-f]{64}$/);
});

test('credential detector catches common prefixes', () => {
  assert.equal(containsCredential('sk-or-v1-test'), true);
  assert.equal(containsCredential('tgp_v1_test'), true);
  assert.equal(containsCredential('nvapi-test'), true);
  assert.equal(containsCredential('jina_test'), true);
  assert.equal(containsCredential('fw_test'), true);
  assert.equal(containsCredential('psk-test'), true);
  assert.equal(containsCredential('nck_live_test'), true);
  assert.equal(containsCredential('fc-test'), true);
  assert.equal(containsCredential('omtx_test'), true);
  assert.equal(containsCredential('jf_live_test'), true);
  assert.equal(containsCredential('plain text'), false);
});

test('default provider registry loads', () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  assert.ok(Array.isArray(providers));
  assert.ok(providers.length > 0);
  const ids = new Set(providers.map(p => p.id));
  assert.equal(ids.size, providers.length);
});

test('default task manifest loads and references real files', () => {
  const tasks = loadTaskManifest(DEFAULT_MANIFEST);
  assert.ok(Array.isArray(tasks));
  assert.ok(tasks.length > 0);
  for (const task of tasks) {
    assert.match(task.id, /^[a-z0-9][a-z0-9-]*$/);
    for (const input of task.input_files) {
      assert.ok(fs.existsSync(path.join(root, input)), input);
    }
    assert.ok(fs.existsSync(path.join(root, task.prompt_file)), task.prompt_file);
  }
});

test('selectProvider prefers a matching preferred provider', () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const tasks = loadTaskManifest(DEFAULT_MANIFEST);
  const task = tasks.find(t => t.id === 'cad-motor-gap-review');
  const provider = selectProvider(task, providers);
  assert.equal(provider.id, 'nvidia-robotics');
});

test('buildPrompt includes advisory boundary, hashes, and file contents', () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const tasks = loadTaskManifest(DEFAULT_MANIFEST);
  const task = tasks[0];
  const provider = selectProvider(task, providers);
  const prompt = buildPrompt(task, provider);
  assert.match(prompt, /## Advisory boundary/);
  assert.match(prompt, /Do not claim owner review/);
  assert.match(prompt, /<<<BEGIN FILE>>>/);
  assert.match(prompt, /<<<END FILE>>>/);
  assert.match(prompt, /sha256=/);
  assert.equal(containsCredential(prompt), false);
});

test('runTask dry-run writes evidence and a record', async () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const tasks = loadTaskManifest(DEFAULT_MANIFEST);
  const task = tasks.find(t => t.id === 'firmware-bringup-checklist');
  const provider = selectProvider(task, providers);
  const evidenceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-orchestration-test-'));
  try {
    const record = await runTask(task, provider, { dryRun: true, evidenceDir });
    assert.equal(record.status, 'success');
    assert.equal(record.task_id, task.id);
    assert.match(record.prompt_sha256, /^[0-9a-f]{64}$/);
    assert.match(record.response_sha256, /^[0-9a-f]{64}$/);
    const output = fs.readFileSync(path.join(evidenceDir, task.output_name), 'utf8');
    assert.match(output, /Dry-run advisory output/);
    const run = JSON.parse(fs.readFileSync(path.join(evidenceDir, `${task.id}.run.json`), 'utf8'));
    assert.equal(run.task_id, task.id);
    assert.equal(run.provider_id, provider.id);
    assert.equal(containsCredential(output), false);
    assert.equal(containsCredential(JSON.stringify(run)), false);
  } finally {
    fs.rmSync(evidenceDir, { recursive: true, force: true });
  }
});

test('loadSecretsFile reads a private file outside the repository', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-keys-'));
  const file = path.join(dir, 'ai-keys.env');
  fs.writeFileSync(file, 'AI_TEST_KEY_1=value-1\nAI_TEST_KEY_2="value 2"\n# comment\n', 'utf8');
  delete process.env.AI_TEST_KEY_1;
  delete process.env.AI_TEST_KEY_2;
  try {
    const result = loadSecretsFile(file);
    assert.equal(result.loaded, 2);
    assert.equal(process.env.AI_TEST_KEY_1, 'value-1');
    assert.equal(process.env.AI_TEST_KEY_2, 'value 2');
  } finally {
    delete process.env.AI_TEST_KEY_1;
    delete process.env.AI_TEST_KEY_2;
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('loadSecretsFile rejects files inside the repository', () => {
  assert.throws(() => loadSecretsFile(path.join(root, 'ai-keys.env')));
});

test('parseArgs accepts documented flags', () => {
  const args = parseArgs(['--task', 'x', '--provider', 'y', '--dry-run']);
  assert.equal(args.task, 'x');
  assert.equal(args.provider, 'y');
  assert.equal(args.dryRun, true);
});

test('parseArgs rejects unknown or conflicting flags', () => {
  assert.throws(() => parseArgs(['--task', 'x', '--provider', 'y', '--dry-run', '--live']));
  assert.throws(() => parseArgs(['--task', 'x', '--provider', 'y']));
  assert.throws(() => parseArgs(['--task', 'x', '--provider', 'y', '--dry-run', '--bogus']));
});
