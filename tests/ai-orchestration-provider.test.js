'use strict';
// Offline tests for the expanded AI orchestration harness.
// No live network calls: fetch is stubbed where dispatch paths are exercised.

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  estimateTokens,
  needsCompaction,
  compactInputs,
  runTask,
  selectProvider,
  loadProviderRegistry,
  loadTaskManifest,
  dispatchProvider,
  callWebSearch,
  callWebRead,
  callScholarSearch,
  writeReviewRecord,
  reviewSidecarPath,
  parseArgs,
  DEFAULT_REGISTRY,
  DEFAULT_MANIFEST,
  CONTEXT_DIR,
  DEFAULT_CONTEXT_BUDGET
} = require('../tools/ai-orchestrate.js');

const root = path.resolve(__dirname, '..');

// Names only — never values. Mirrors the key families in the owner's private key store.
const KEY_STORE_NAMES = [
  'ANSWERS_API_KEY', 'ATLAS_CLOUD_API_KEY', 'BASETEN_API_KEY', 'BRAVE_SEARCH_API_KEY',
  'CORE_API_KEY', 'DEEPINFRA_API_KEY', 'EXA_API_KEY', 'FIRECRAWL_API_KEY', 'FIREWORKS_API_KEY',
  'INCEPTION_API_KEY', 'JAPANFOLD_API_KEY', 'JINA_API_KEY', 'LLMTR_API_KEY', 'MODAL_TOKEN_ID',
  'MODAL_TOKEN_SECRET', 'MOONSHOT_API_KEY', 'NCBI_API_KEY', 'NOVITA_API_KEY', 'NVIDIA_API_KEY',
  'OMTX_API_KEY', 'OPENALEX_API_KEY', 'OPENROUTER_API_KEY', 'ORCID_CLIENT_ID', 'ORCID_CLIENT_SECRET',
  'PARASAIL_API_KEY', 'SEMANTIC_SCHOLAR_API_KEY', 'SILICONFLOW_API_KEY', 'TOGETHER_API_KEY'
];

function stubFetch(handler) {
  const original = global.fetch;
  global.fetch = handler;
  return () => { global.fetch = original; };
}

function realTask(id) {
  return loadTaskManifest(DEFAULT_MANIFEST).find(t => t.id === id);
}

test('registry covers every key family in the private store', () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const names = new Set(providers.map(p => p.auth_env));
  const secondary = { MODAL_TOKEN_SECRET: 'MODAL_TOKEN_ID', ORCID_CLIENT_SECRET: 'ORCID_CLIENT_ID' };
  for (const name of KEY_STORE_NAMES) {
    assert.ok(names.has(name) || names.has(secondary[name]), `missing provider for ${name}`);
  }
});

test('registry entries satisfy the extended schema', () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  assert.ok(providers.length >= 25);
  const byId = Object.fromEntries(providers.map(p => [p.id, p]));
  assert.equal(byId['baseten-text'].auth_env, 'BASETEN_API_KEY');
  assert.equal(byId['exa-search'].family, 'web-search');
  assert.equal(byId['openalex-search'].family, 'scholar');
  assert.equal(byId['modal-runtime'].transport, 'planned');
  assert.equal(byId['modal-runtime'].endpoint, null);
});

test('real registry routes each task family to a live provider of that family', () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const pick = id => selectProvider(realTask(id), providers);
  assert.equal(pick('cad-motor-gap-review').id, 'nvidia-robotics');
  assert.equal(pick('rules-update-scan').id, 'exa-search');
  assert.equal(pick('vendor-cad-research').id, 'exa-search');
  assert.equal(pick('literature-search').id, 'openalex-search');
  assert.equal(pick('vendor-page-read').id, 'jina-read');
});

test('selectProvider picks the cheapest matching provider without a preference match', () => {
  const providers = [
    { id: 'p-expensive', family: 'chat', role: ['review'], endpoint: 'https://a.example/v1', auth_env: 'A1', transport: 'openai-compat', model_hint: 'm', cost_rank: 5, max_context_tokens: 1000 },
    { id: 'p-cheap', family: 'chat', role: ['review'], endpoint: 'https://b.example/v1', auth_env: 'B1', transport: 'openai-compat', model_hint: 'm', cost_rank: 1, max_context_tokens: 1000 }
  ];
  const task = { id: 't', kind: 'review', preferred_providers: ['absent'], input_files: [], prompt_file: 'x', output_name: 'o', title: 'T' };
  assert.equal(selectProvider(task, providers).id, 'p-cheap');
});

test('preferred provider order wins over cost ranking', () => {
  const providers = [
    { id: 'p-expensive', family: 'chat', role: ['review'], endpoint: 'https://a.example/v1', auth_env: 'A1', transport: 'openai-compat', model_hint: 'm', cost_rank: 5, max_context_tokens: 1000 },
    { id: 'p-cheap', family: 'chat', role: ['review'], endpoint: 'https://b.example/v1', auth_env: 'B1', transport: 'openai-compat', model_hint: 'm', cost_rank: 1, max_context_tokens: 1000 }
  ];
  const task = { id: 't', kind: 'review', preferred_providers: ['p-expensive'], input_files: [], prompt_file: 'x', output_name: 'o', title: 'T' };
  assert.equal(selectProvider(task, providers).id, 'p-expensive');
});

test('planned transports and mismatched families are never auto-selected', () => {
  const providers = [
    { id: 'p-planned', family: 'web-search', role: ['search'], endpoint: null, auth_env: 'A1', transport: 'planned', model_hint: null, cost_rank: 1, max_context_tokens: 1000 },
    { id: 'p-wrong-family', family: 'chat', role: ['search'], endpoint: 'https://c.example/v1', auth_env: 'C1', transport: 'openai-compat', model_hint: 'm', cost_rank: 1, max_context_tokens: 1000 }
  ];
  const task = { id: 't', kind: 'search', preferred_providers: [], input_files: [], prompt_file: 'x', output_name: 'o', title: 'T' };
  assert.throws(() => selectProvider(task, providers), /no provider for kind search/);
});

test('estimateTokens and needsCompaction use a length heuristic', () => {
  assert.equal(estimateTokens('x'.repeat(400)), 100);
  assert.equal(estimateTokens(''), 1);
  assert.ok(needsCompaction('x'.repeat(40001), 10000));
  assert.equal(needsCompaction('x'.repeat(40000), 10000), false);
});

test('compactInputs does nothing within the budget', async () => {
  const task = realTask('organizer-qa-draft');
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const provider = selectProvider(task, providers);
  const result = await compactInputs(task, provider, { contextBudget: DEFAULT_CONTEXT_BUDGET, dryRun: true });
  assert.equal(result.applied, false);
});

test('compactInputs over budget writes a deterministic offline digest', async () => {
  const task = realTask('organizer-qa-draft');
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const provider = selectProvider(task, providers);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-orchestration-ctx-'));
  try {
    const first = await compactInputs(task, provider, { contextBudget: 10, contextDir: dir, dryRun: true });
    const second = await compactInputs(task, provider, { contextBudget: 10, contextDir: dir, dryRun: true });
    assert.equal(first.applied, true);
    assert.equal(first.digestSha256, second.digestSha256);
    assert.ok(first.originalTokens > 10);
    assert.ok(fs.existsSync(path.join(dir, 'organizer-qa-draft.digest.md')));
    assert.match(first.digest, /lines omitted by local compaction/);
    const totalChars = task.input_files.reduce((sum, f) => sum + fs.readFileSync(path.join(root, f), 'utf8').length, 0);
    assert.ok(first.digest.length < totalChars);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('no-compact and context_policy off disable compaction', async () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const disabled = await compactInputs(realTask('vendor-page-read'), providers[0], { contextBudget: 1, dryRun: true });
  assert.equal(disabled.applied, false);
  const suppressed = await compactInputs(realTask('rules-update-scan'), providers[0], { contextBudget: 1, noCompact: true, dryRun: true });
  assert.equal(suppressed.applied, false);
});

test('runTask records compaction and review fields in the run record', async () => {
  const task = realTask('organizer-qa-draft');
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const provider = selectProvider(task, providers);
  const evidenceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-orchestration-ev-'));
  const contextDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-orchestration-cx-'));
  try {
    const record = await runTask(task, provider, { dryRun: true, contextBudget: 5, evidenceDir, contextDir });
    assert.equal(record.status, 'success');
    assert.equal(record.provider_family, 'chat');
    assert.equal(record.compaction.applied, true);
    assert.match(record.compaction.digest_file, /organizer-qa-draft\.digest\.md$/);
    assert.match(record.compaction.digest_sha256, /^[0-9a-f]{64}$/);
    assert.ok(record.input_files.every(f => f.compacted === true));
    assert.equal(record.review.status, 'pending');
    assert.match(record.review.run_sha256, /^[0-9a-f]{64}$/);
  } finally {
    fs.rmSync(evidenceDir, { recursive: true, force: true });
    fs.rmSync(contextDir, { recursive: true, force: true });
  }
});

test('review workflow writes a sidecar and mirrors into the run record', async () => {
  const task = realTask('firmware-bringup-checklist');
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const provider = selectProvider(task, providers);
  const evidenceDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-orchestration-rv-'));
  try {
    await runTask(task, provider, { dryRun: true, evidenceDir });
    const accepted = writeReviewRecord(task, null, { status: 'accepted', notes: 'planning only' }, { evidenceDir });
    assert.equal(accepted.status, 'accepted');
    assert.ok(fs.existsSync(reviewSidecarPath(task, evidenceDir)));
    const run = JSON.parse(fs.readFileSync(path.join(evidenceDir, `${task.id}.run.json`), 'utf8'));
    assert.equal(run.review.status, 'accepted');
    assert.equal(run.review.reviewer, 'owner');
    const rejected = writeReviewRecord(task, null, { status: 'rejected', notes: 'nope' }, { evidenceDir });
    assert.equal(rejected.status, 'rejected');
    assert.throws(() => writeReviewRecord(task, null, { status: 'bogus' }, { evidenceDir }), /accepted or rejected/);
  } finally {
    fs.rmSync(evidenceDir, { recursive: true, force: true });
  }
});

test('reviewing a task with no run record fails clearly', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-orchestration-nr-'));
  try {
    assert.throws(() => writeReviewRecord({ id: 'never-ran' }, null, { status: 'accepted' }, { evidenceDir: dir }), /no run record/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('callWebSearch formats exa results and sends the x-api-key header', async () => {
  process.env.EXA_API_KEY = 'unit-test-key';
  let captured = null;
  const restore = stubFetch(async (url, init) => {
    captured = { url, init };
    return { ok: true, status: 200, statusText: 'OK', json: async () => ({ results: [{ title: 'Rules update', url: 'https://example.com/r', text: 'field dimensions changed' }] }) };
  });
  try {
    const providers = loadProviderRegistry(DEFAULT_REGISTRY);
    const exa = providers.find(p => p.id === 'exa-search');
    const out = await callWebSearch(exa, 'test query');
    assert.match(out, /Rules update/);
    assert.match(out, /https:\/\/example\.com\/r/);
    assert.equal(captured.init.headers['x-api-key'], 'unit-test-key');
  } finally {
    restore();
    delete process.env.EXA_API_KEY;
  }
});

test('brave search uses the subscription token header', async () => {
  process.env.BRAVE_SEARCH_API_KEY = 'unit-test-key';
  let captured = null;
  const restore = stubFetch(async (url, init) => {
    captured = { url, init };
    return { ok: true, status: 200, statusText: 'OK', json: async () => ({ web: { results: [{ title: 'Brave hit', url: 'https://example.com/b', description: 'desc' }] } }) };
  });
  try {
    const providers = loadProviderRegistry(DEFAULT_REGISTRY);
    const brave = providers.find(p => p.id === 'brave-search');
    const out = await callWebSearch(brave, 'test query');
    assert.match(out, /Brave hit/);
    assert.match(captured.url, /web\/search\?q=/);
    assert.equal(captured.init.headers['X-Subscription-Token'], 'unit-test-key');
  } finally {
    restore();
    delete process.env.BRAVE_SEARCH_API_KEY;
  }
});

test('dispatchProvider routes web-search and web-read transports', async () => {
  process.env.JINA_API_KEY = 'unit-test-key';
  let requested = null;
  const restore = stubFetch(async (url) => {
    requested = url;
    return { ok: true, status: 200, statusText: 'OK', text: async () => '# markdown results' };
  });
  try {
    const providers = loadProviderRegistry(DEFAULT_REGISTRY);
    const jinaSearch = providers.find(p => p.id === 'jina-search');
    const out = await dispatchProvider(jinaSearch, { query: 'q', title: 't' }, {});
    assert.match(out, /markdown results/);
    assert.match(requested, /s\.jina\.ai\/\?q=/);
    const jinaRead = providers.find(p => p.id === 'jina-read');
    const page = await dispatchProvider(jinaRead, { query: 'https://example.com/page', title: 't' }, {});
    assert.match(page, /markdown results/);
  } finally {
    restore();
    delete process.env.JINA_API_KEY;
  }
});

test('scholar-search dispatch reaches the semantic scholar endpoint', async () => {
  process.env.SEMANTIC_SCHOLAR_API_KEY = 'unit-test-key';
  let captured = null;
  const restore = stubFetch(async (url, init) => {
    captured = { url, init };
    return { ok: true, status: 200, statusText: 'OK', json: async () => ({ data: [{ title: 'Odometry paper', year: 2020, url: 'https://example.com/p', externalIds: {} }] }) };
  });
  try {
    const providers = loadProviderRegistry(DEFAULT_REGISTRY);
    const s2 = providers.find(p => p.id === 'semantic-scholar-search');
    const out = await dispatchProvider(s2, { query: 'odometry', title: 't' }, {});
    assert.match(out, /Odometry paper/);
    assert.match(captured.url, /paper\/search\?/);
    assert.equal(captured.init.headers['x-api-key'], 'unit-test-key');
  } finally {
    restore();
    delete process.env.SEMANTIC_SCHOLAR_API_KEY;
  }
});

test('planned transports fail with a clear message', async () => {
  const providers = loadProviderRegistry(DEFAULT_REGISTRY);
  const modal = providers.find(p => p.id === 'modal-runtime');
  await assert.rejects(() => dispatchProvider(modal, { query: 'x', title: 't' }, {}), /planned, not live/);
  const inception = providers.find(p => p.id === 'inception-lab');
  await assert.rejects(() => dispatchProvider(inception, { title: 't' }, { prompt: 'p' }), /planned, not live/);
});

test('parseArgs handles compaction and review flags', () => {
  const run = parseArgs(['--task', 'x', '--provider', 'y', '--dry-run', '--context-budget', '500', '--no-compact']);
  assert.equal(run.contextBudget, 500);
  assert.equal(run.noCompact, true);
  const review = parseArgs(['--review', '--task', 'x', '--status', 'rejected', '--notes', 'not yet']);
  assert.equal(review.review, true);
  assert.equal(review.status, 'rejected');
  assert.equal(review.notes, 'not yet');
  assert.equal(review.provider, null);
  assert.throws(() => parseArgs(['--review', '--task', 'x']));
  assert.throws(() => parseArgs(['--review', '--task', 'x', '--status', 'accepted', '--live']));
  assert.throws(() => parseArgs(['--task', 'x', '--status', 'accepted']));
  assert.throws(() => parseArgs(['--task', 'x', '--provider', 'y', '--dry-run', '--context-budget', 'abc']));
});
