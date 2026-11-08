#!/usr/bin/env node
'use strict';
// AI orchestration harness: routes narrowly scoped engineering tasks to the best-suited provider
// and records auditable, advisory evidence. Never stores credentials.
// Agent-built tooling for the owner's hobby/learning project.
//
// Transports:
//   openai-compat / openai-chat  OpenAI-compatible chat completions
//   web-search / web-read        search and page-read APIs (Exa, Brave, Jina, Firecrawl)
//   scholar-search               literature APIs (OpenAlex, Semantic Scholar, CORE, PubMed, ORCID)
//   runtime / planned            registered but not live; never auto-selected

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const os = require('node:os');

const ROOT = path.resolve(__dirname, '..');
const DEFAULT_REGISTRY = path.join(ROOT, 'derived/ai-orchestration/registry.json');
const DEFAULT_MANIFEST = path.join(ROOT, 'derived/ai-orchestration/tasks.json');
const EVIDENCE_DIR = path.join(ROOT, 'derived/ai-orchestration/evidence');
const CONTEXT_DIR = path.join(ROOT, 'derived/ai-orchestration/context');
const COMPACTION_PROMPT = path.join(ROOT, 'prompts/context-compaction.md');
const DEFAULT_SECRETS_FILE = path.join(os.homedir(), '.config', 'ai-keys.env');
// Default context budget in estimated tokens. The owner asked that assembled prompts stay
// well below 200k-token context windows; 12000 keeps prompts small and cheap by default.
const DEFAULT_CONTEXT_BUDGET = 12000;
const MAX_RESPONSE_CHARS = 20000;

const PROVIDER_FIELDS = ['id', 'role', 'endpoint', 'auth_env', 'transport', 'model_hint'];
const TASK_FIELDS = ['id', 'kind', 'title', 'input_files', 'prompt_file', 'preferred_providers', 'output_name'];

const FAMILIES = ['chat', 'web-search', 'web-read', 'scholar', 'runtime', 'planned'];
const TRANSPORTS = ['openai-compat', 'openai-chat', 'web-search', 'web-read', 'scholar-search', 'runtime', 'planned'];
const CHAT_TRANSPORTS = ['openai-compat', 'openai-chat'];
const TASK_KINDS = ['chat', 'summarize', 'review', 'research', 'search', 'literature', 'vision', 'code', 'planning', 'runtime'];
const REVIEW_STATUSES = ['accepted', 'rejected', 'pending'];
const FAMILY_FOR_KIND = {
  chat: 'chat',
  summarize: 'chat',
  review: 'chat',
  code: 'chat',
  planning: 'chat',
  vision: 'chat',
  search: 'web-search',
  research: 'web-read',
  literature: 'scholar',
  runtime: 'runtime'
};

const CREDENTIAL_PATTERNS = [
  /sk-or-v1-/i,
  /tgp_v1_/i,
  /nvapi-/i,
  /jina_[0-9a-z]/,
  /fw_/i,
  /psk-/i,
  /nck_live_/i,
  /fc-/i,
  /omtx_[0-9a-z]/,
  /jf_live_/i,
  /s2k-/i,
  /apikey-[a-f0-9]/i,
  /sk_[A-Za-z0-9]{16}/,
  /ak-[A-Za-z0-9]{20}/
];

function sha256(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function containsCredential(text) {
  return CREDENTIAL_PATTERNS.some(p => p.test(text));
}

function readJsonFile(file) {
  const raw = fs.readFileSync(file, 'utf8');
  if (containsCredential(raw)) {
    throw new Error(`credential-like content found in ${file}`);
  }
  return JSON.parse(raw);
}

function loadSecretsFile(file = DEFAULT_SECRETS_FILE) {
  if (!file) {
    return { path: null, loaded: 0 };
  }
  const resolved = path.resolve(file);
  if (resolved === ROOT || resolved.startsWith(ROOT + path.sep)) {
    throw new Error('secrets file must live outside the repository');
  }
  if (!fs.existsSync(resolved)) {
    return { path: resolved, loaded: 0 };
  }
  const raw = fs.readFileSync(resolved, 'utf8');
  const lines = raw.split(/\r?\n/);
  let loaded = 0;
  for (const line of lines) {
    const match = /^([A-Z][A-Z0-9_]*)\s*=\s*(.*)$/.exec(line.trim());
    if (!match) continue;
    const key = match[1];
    const value = match[2].replace(/^["']|["']$/g, '');
    if (!process.env[key]) {
      process.env[key] = value;
      loaded += 1;
    }
  }
  return { path: resolved, loaded };
}

function estimateTokens(text) {
  return Math.max(1, Math.ceil(String(text).length / 4));
}

function needsCompaction(prompt, budgetTokens) {
  return estimateTokens(prompt) > budgetTokens;
}

function clip(text, maxChars = MAX_RESPONSE_CHARS) {
  const value = String(text);
  if (value.length <= maxChars) return value;
  return `${value.slice(0, maxChars)}\n[... clipped at ${maxChars} characters ...]`;
}

function parsePositiveInt(value, flag) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1) {
    throw new Error(`${flag} must be a positive integer`);
  }
  return n;
}

function validateProvider(provider) {
  if (!provider || typeof provider !== 'object') {
    throw new Error('provider must be an object');
  }
  for (const field of ['id', 'role', 'auth_env', 'transport', 'family', 'cost_rank', 'max_context_tokens']) {
    if (provider[field] === undefined || provider[field] === null) {
      throw new Error(`provider missing field ${field}`);
    }
  }
  if (!Array.isArray(provider.role) || provider.role.length === 0) {
    throw new Error(`provider ${provider.id}: role must be a non-empty array`);
  }
  if (!FAMILIES.includes(provider.family)) {
    throw new Error(`provider ${provider.id}: unknown family ${provider.family}`);
  }
  if (!TRANSPORTS.includes(provider.transport)) {
    throw new Error(`provider ${provider.id}: unknown transport ${provider.transport}`);
  }
  if (typeof provider.endpoint !== 'string' || !/^https?:\/\//.test(provider.endpoint)) {
    if (provider.transport !== 'planned') {
      throw new Error(`provider ${provider.id}: endpoint must be an http(s) URL`);
    }
  }
  if (!Number.isInteger(provider.cost_rank) || provider.cost_rank < 1 || provider.cost_rank > 5) {
    throw new Error(`provider ${provider.id}: cost_rank must be an integer 1-5`);
  }
  if (!Number.isInteger(provider.max_context_tokens) || provider.max_context_tokens < 1) {
    throw new Error(`provider ${provider.id}: max_context_tokens must be a positive integer`);
  }
  if (!/^[A-Z][A-Z0-9_]*$/.test(provider.auth_env)) {
    throw new Error(`provider ${provider.id}: auth_env must be an environment-variable name`);
  }
  if (CHAT_TRANSPORTS.includes(provider.transport) && (typeof provider.model_hint !== 'string' || provider.model_hint.length === 0)) {
    throw new Error(`provider ${provider.id}: chat providers need a model_hint`);
  }
  if (provider.notes !== undefined && typeof provider.notes !== 'string') {
    throw new Error(`provider ${provider.id}: notes must be a string`);
  }
}

function validateTask(task) {
  if (!task || typeof task !== 'object') {
    throw new Error('task must be an object');
  }
  for (const field of TASK_FIELDS) {
    if (task[field] === undefined) {
      throw new Error(`task missing field ${field}`);
    }
  }
  if (!Array.isArray(task.input_files) || task.input_files.length === 0) {
    throw new Error(`task ${task.id}: input_files must be a non-empty array`);
  }
  if (!Array.isArray(task.preferred_providers)) {
    throw new Error(`task ${task.id}: preferred_providers must be an array`);
  }
  if (!/^[a-z0-9][a-z0-9-]*$/.test(task.id)) {
    throw new Error(`task ${task.id}: id must be lowercase and hyphenated`);
  }
  if (!TASK_KINDS.includes(task.kind)) {
    throw new Error(`task ${task.id}: unknown kind ${task.kind}`);
  }
  if (task.context_policy !== undefined) {
    const policy = task.context_policy;
    if (!policy || typeof policy !== 'object') {
      throw new Error(`task ${task.id}: context_policy must be an object`);
    }
    if (policy.mode !== undefined && !['auto', 'off'].includes(policy.mode)) {
      throw new Error(`task ${task.id}: context_policy.mode must be auto or off`);
    }
    if (policy.budget_tokens !== undefined && (!Number.isInteger(policy.budget_tokens) || policy.budget_tokens < 1)) {
      throw new Error(`task ${task.id}: context_policy.budget_tokens must be a positive integer`);
    }
  }
  if (task.query !== undefined && typeof task.query !== 'string') {
    throw new Error(`task ${task.id}: query must be a string`);
  }
}

// Follow-up from the 2026-11-07 study pack: the JSON task-object validator.
// validateTask checks one task object in isolation; this cross-validates the
// manifest against the provider registry and the fields validateTask leaves
// shallow, so a bad tasks.json edit fails before any run or review happens.
const QUERY_REQUIRED_FAMILIES = ['web-search', 'web-read', 'scholar'];

function isRelativeInsideRepo(relativePath) {
  return typeof relativePath === 'string'
    && relativePath.length > 0
    && !path.isAbsolute(relativePath)
    && !relativePath.split(/[/\\]/).includes('..');
}

function validateTaskManifest(tasks, providers) {
  if (!Array.isArray(tasks)) {
    throw new Error('task manifest must be a JSON array');
  }
  if (!Array.isArray(providers)) {
    throw new Error('provider registry must be a JSON array');
  }
  const providerIds = new Set(providers.map(provider => provider.id));
  for (const task of tasks) {
    if (typeof task.title !== 'string' || task.title.trim().length === 0) {
      throw new Error(`task ${task.id}: title must be a non-empty string`);
    }
    if (task.owner_review !== undefined && typeof task.owner_review !== 'boolean') {
      throw new Error(`task ${task.id}: owner_review must be a boolean`);
    }
    if (typeof task.output_name !== 'string'
      || !/^[A-Za-z0-9][A-Za-z0-9._-]*\.md$/.test(task.output_name)
      || task.output_name.includes('..')) {
      throw new Error(`task ${task.id}: output_name must be a safe .md file name without path separators`);
    }
    if (task.preferred_providers.length === 0
      || task.preferred_providers.some(id => typeof id !== 'string')) {
      throw new Error(`task ${task.id}: preferred_providers must be a non-empty array of provider ids`);
    }
    for (const id of task.preferred_providers) {
      if (!providerIds.has(id)) {
        throw new Error(`task ${task.id}: unknown preferred provider ${id}`);
      }
    }
    const preferred = task.preferred_providers.map(id => providers.find(provider => provider.id === id));
    if (!preferred.some(provider => isSelectable(provider, task))) {
      throw new Error(`task ${task.id}: no preferred provider is a live route for kind ${task.kind}`);
    }
    const family = FAMILY_FOR_KIND[task.kind];
    if (family && QUERY_REQUIRED_FAMILIES.includes(family)
      && (typeof task.query !== 'string' || task.query.trim().length === 0)) {
      throw new Error(`task ${task.id}: kind ${task.kind} requires a non-empty query`);
    }
    if (!isRelativeInsideRepo(task.prompt_file)) {
      throw new Error(`task ${task.id}: prompt_file must be a relative path inside the repository`);
    }
    for (const input of task.input_files) {
      if (!isRelativeInsideRepo(input)) {
        throw new Error(`task ${task.id}: input file ${input} must be a relative path inside the repository`);
      }
    }
  }
  return tasks;
}

function loadProviderRegistry(file = DEFAULT_REGISTRY) {
  const data = readJsonFile(file);
  if (!Array.isArray(data)) {
    throw new Error('provider registry must be a JSON array');
  }
  const ids = new Set();
  for (const provider of data) {
    validateProvider(provider);
    if (ids.has(provider.id)) {
      throw new Error(`duplicate provider id ${provider.id}`);
    }
    ids.add(provider.id);
  }
  return data;
}

function loadTaskManifest(file = DEFAULT_MANIFEST) {
  const data = readJsonFile(file);
  if (!Array.isArray(data)) {
    throw new Error('task manifest must be a JSON array');
  }
  const ids = new Set();
  for (const task of data) {
    validateTask(task);
    if (ids.has(task.id)) {
      throw new Error(`duplicate task id ${task.id}`);
    }
    for (const input of task.input_files) {
      const inputPath = path.join(ROOT, input);
      if (!fs.existsSync(inputPath)) {
        throw new Error(`task ${task.id}: missing input file ${input}`);
      }
    }
    const promptPath = path.join(ROOT, task.prompt_file);
    if (!fs.existsSync(promptPath)) {
      throw new Error(`task ${task.id}: missing prompt file ${task.prompt_file}`);
    }
    ids.add(task.id);
  }
  return data;
}

function isSelectable(provider, task) {
  if (provider.transport === 'planned') {
    return false;
  }
  if (!Array.isArray(provider.role) || !provider.role.includes(task.kind)) {
    return false;
  }
  const family = FAMILY_FOR_KIND[task.kind];
  if (family && provider.family !== family) {
    return false;
  }
  return true;
}

function selectProvider(task, providers) {
  const preferred = providers.filter(p => task.preferred_providers.includes(p.id) && isSelectable(p, task));
  if (preferred.length > 0) {
    return preferred[0];
  }
  const matching = providers.map((provider, index) => ({ provider, index })).filter(x => isSelectable(x.provider, task));
  if (matching.length === 0) {
    throw new Error(`task ${task.id}: no provider for kind ${task.kind}`);
  }
  matching.sort((a, b) => (a.provider.cost_rank - b.provider.cost_rank) || (a.index - b.index));
  return matching[0].provider;
}

function buildPrompt(task, provider, options = {}) {
  const promptPath = path.join(ROOT, task.prompt_file);
  const template = fs.readFileSync(promptPath, 'utf8');
  let inputBlocks;
  if (options.compaction && options.compaction.applied) {
    inputBlocks = [
      '### Input digest (compacted; the original files were replaced to fit the context budget)',
      `digest_sha256=${options.compaction.digestSha256}`,
      '<<<BEGIN FILE>>>',
      options.compaction.digest,
      '<<<END FILE>>>'
    ].join('\n');
  } else {
    inputBlocks = task.input_files.map(input => {
      const inputPath = path.join(ROOT, input);
      const content = fs.readFileSync(inputPath, 'utf8');
      return [
        `### Input file: ${input}`,
        `sha256=${sha256(content)}`,
        '<<<BEGIN FILE>>>',
        content,
        '<<<END FILE>>>'
      ].join('\n');
    }).join('\n\n');
  }
  const prompt = [
    template.trim(),
    '',
    '## Input files',
    inputBlocks,
    '',
    '## Provider hint',
    `provider_id=${provider.id}`,
    `model_hint=${provider.model_hint ?? 'n/a'}`,
    '',
    '## Advisory boundary',
    'This output is agent-run and advisory. Do not claim owner review, physical testing, or competition qualification.'
  ].join('\n');
  if (containsCredential(prompt)) {
    throw new Error(`prompt for task ${task.id} contains credential-like content`);
  }
  return prompt;
}

function runRecordFileName(task) {
  return `${task.id}.run.json`;
}

async function callOpenAICompatible(provider, prompt, options) {
  const apiKey = process.env[provider.auth_env];
  if (!apiKey) {
    throw new Error(`missing environment variable ${provider.auth_env} for provider ${provider.id}`);
  }
  const response = await fetch(provider.endpoint, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: provider.model_hint,
      messages: [
        { role: 'system', content: 'You are a careful engineering advisor. Be concise and cite evidence paths.' },
        { role: 'user', content: prompt }
      ],
      temperature: options.temperature ?? 0.2,
      max_tokens: provider.max_tokens_hint ?? options.maxTokens ?? 2048
    })
  });
  if (!response.ok) {
    throw new Error(`${provider.id} request failed: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  const content = data?.choices?.[0]?.message?.content;
  if (typeof content !== 'string' || content.trim().length === 0) {
    throw new Error(`${provider.id} returned an empty completion`);
  }
  return content.trim();
}

function dryRunResponse(task, provider, prompt) {
  return [
    '# Dry-run advisory output',
    '',
    `task_id: ${task.id}`,
    `provider_id: ${provider.id}`,
    `model_hint: ${provider.model_hint ?? 'n/a'}`,
    `prompt_sha256: ${sha256(prompt)}`,
    '',
    'This is a deterministic dry-run. No network request was made and no provider credentials were used.',
    '',
    'Next owner action: review this plan, then enable a live provider with the corresponding environment variable.'
  ].join('\n');
}

function localDigest(task) {
  const blocks = task.input_files.map(input => {
    const inputPath = path.join(ROOT, input);
    const content = fs.readFileSync(inputPath, 'utf8');
    const lines = content.split('\n');
    const head = lines.slice(0, 30);
    const tail = lines.length > 45 ? lines.slice(-10) : [];
    const omitted = Math.max(0, lines.length - head.length - tail.length);
    const parts = [
      `### Input file: ${input}`,
      `sha256=${sha256(content)}`,
      `chars=${content.length} tokens_estimated=${estimateTokens(content)} lines=${lines.length}`,
      '<<<BEGIN FILE>>>',
      head.join('\n')
    ];
    if (omitted > 0) {
      parts.push(`[... ${omitted} lines omitted by local compaction ...]`);
    }
    if (tail.length > 0) {
      parts.push(tail.join('\n'));
    }
    parts.push('<<<END FILE>>>');
    return parts.join('\n');
  });
  return blocks.join('\n\n');
}

function contextBudgetFor(task, options) {
  if (task.context_policy && Number.isInteger(task.context_policy.budget_tokens)) {
    return task.context_policy.budget_tokens;
  }
  return Number.isInteger(options.contextBudget) ? options.contextBudget : DEFAULT_CONTEXT_BUDGET;
}

async function compactInputs(task, provider, options = {}) {
  const mode = (task.context_policy && task.context_policy.mode) || 'auto';
  if (mode === 'off' || options.noCompact) {
    return { applied: false, reason: 'disabled' };
  }
  const budget = contextBudgetFor(task, options);
  const fullPrompt = buildPrompt(task, provider);
  if (!needsCompaction(fullPrompt, budget)) {
    return { applied: false, reason: 'within budget' };
  }
  const contextDir = options.contextDir || CONTEXT_DIR;
  fs.mkdirSync(contextDir, { recursive: true });
  const digestPath = path.join(contextDir, `${task.id}.digest.md`);
  let digest;
  let compactionProviderId;
  let reason = 'prompt exceeded context budget';
  if (options.dryRun) {
    digest = localDigest(task);
    compactionProviderId = 'local-deterministic-digest';
    reason = 'dry-run: deterministic local digest';
  } else {
    const providers = loadProviderRegistry(options.registry || DEFAULT_REGISTRY);
    const candidates = providers
      .filter(p => CHAT_TRANSPORTS.includes(p.transport) && p.role.includes('summarize') && process.env[p.auth_env])
      .sort((a, b) => a.cost_rank - b.cost_rank);
    if (candidates.length === 0) {
      digest = localDigest(task);
      compactionProviderId = 'local-deterministic-digest';
      reason = 'no credentialed summarize provider; used local digest';
    } else {
      const summarizeProvider = candidates[0];
      digest = await callOpenAICompatible(summarizeProvider, buildPrompt(task, summarizeProvider), options);
      compactionProviderId = summarizeProvider.id;
    }
  }
  fs.writeFileSync(digestPath, `${digest}\n`, 'utf8');
  return {
    applied: true,
    digest,
    digestPath,
    digestFile: path.relative(ROOT, digestPath),
    digestSha256: sha256(digest),
    compactionProviderId,
    reason,
    originalTokens: estimateTokens(fullPrompt),
    budgetTokens: budget
  };
}

async function runTask(task, provider, options = { dryRun: true }) {
  if (!task || !provider) {
    throw new Error('task and provider are required');
  }
  const startedAt = new Date().toISOString();
  const compaction = await compactInputs(task, provider, options);
  const prompt = compaction.applied
    ? buildPrompt(task, provider, { compaction })
    : buildPrompt(task, provider);
  let output;
  let status = 'success';
  try {
    output = options.dryRun
      ? dryRunResponse(task, provider, prompt)
      : await dispatchProvider(provider, task, { ...options, prompt });
  } catch (error) {
    status = 'error';
    output = `# AI orchestration failure\n\n${String(error && error.message ? error.message : error)}\n`;
  }
  const finishedAt = new Date().toISOString();
  const evidenceDir = options.evidenceDir || EVIDENCE_DIR;
  const evidencePath = path.join(evidenceDir, task.output_name);
  const recordPath = path.join(evidenceDir, runRecordFileName(task));
  fs.mkdirSync(path.dirname(evidencePath), { recursive: true });
  fs.writeFileSync(evidencePath, `${output}\n`, 'utf8');
  const promptSha = sha256(prompt);
  const responseSha = sha256(output);
  const record = {
    task_id: task.id,
    provider_id: provider.id,
    provider_family: provider.family,
    cost_rank: provider.cost_rank,
    model: provider.model_hint,
    started_at: startedAt,
    finished_at: finishedAt,
    status,
    prompt_sha256: promptSha,
    response_sha256: responseSha,
    input_files: task.input_files.map(input => {
      const content = fs.readFileSync(path.join(ROOT, input), 'utf8');
      return {
        path: input,
        sha256: sha256(content),
        chars: content.length,
        tokens_estimated: estimateTokens(content),
        compacted: compaction.applied
      };
    }),
    compaction: compaction.applied ? {
      applied: true,
      digest_file: compaction.digestFile,
      digest_sha256: compaction.digestSha256,
      compaction_provider_id: compaction.compactionProviderId,
      reason: compaction.reason
    } : { applied: false },
    output_path: path.relative(ROOT, evidencePath),
    review: {
      status: 'pending',
      reviewer: null,
      reviewed_at: null,
      notes: null,
      run_sha256: sha256(`${promptSha}\n${responseSha}\n${status}`),
      output_sha256: responseSha
    },
    notes: 'Agent-run; not owner-reviewed.'
  };
  fs.writeFileSync(recordPath, `${JSON.stringify(record, null, 2)}\n`, 'utf8');
  return record;
}

function formatSearchItems(items) {
  return items.map(item => {
    const title = item.title || item.name || item.heading || '(untitled)';
    const url = item.url || item.link || item.id || '';
    const snippet = item.text || item.description || item.snippet || item.summary || '';
    const compact = String(snippet).replace(/\s+/g, ' ').trim().slice(0, 400);
    return `- ${title}${url ? ` — ${url}` : ''}${compact ? `\n  ${compact}` : ''}`;
  }).join('\n');
}

async function requireOk(response, provider) {
  if (!response.ok) {
    throw new Error(`${provider.id} request failed: ${response.status} ${response.statusText}`);
  }
  return response;
}

async function callWebSearch(provider, query, options = {}) {
  const limit = Math.max(1, Math.min(options.limit ?? 8, 20));
  const apiKey = process.env[provider.auth_env];
  if (!apiKey) {
    throw new Error(`missing environment variable ${provider.auth_env} for provider ${provider.id}`);
  }
  if (provider.id === 'exa-search') {
    const response = await requireOk(await fetch('https://api.exa.ai/search', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': apiKey },
      body: JSON.stringify({ query, numResults: limit, contents: { text: { maxCharacters: 1000 } } })
    }), provider);
    const data = await response.json();
    return clip(formatSearchItems(data.results || []));
  }
  if (provider.id === 'brave-search') {
    const url = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(query)}&count=${limit}`;
    const response = await requireOk(await fetch(url, {
      headers: { 'X-Subscription-Token': apiKey, accept: 'application/json' }
    }), provider);
    const data = await response.json();
    return clip(formatSearchItems((data.web && data.web.results) || []));
  }
  if (provider.id === 'brave-answers') {
    const url = `https://api.search.brave.com/res/v1/answers/search?q=${encodeURIComponent(query)}`;
    const response = await requireOk(await fetch(url, {
      headers: { 'X-Subscription-Token': apiKey, accept: 'application/json' }
    }), provider);
    const data = await response.json();
    const items = (data.answers && (data.answers.results || data.answers.items)) || data.results || [];
    return clip(formatSearchItems(items));
  }
  if (provider.id === 'jina-search') {
    const url = `https://s.jina.ai/?q=${encodeURIComponent(query)}`;
    const response = await requireOk(await fetch(url, {
      headers: { Authorization: `Bearer ${apiKey}` }
    }), provider);
    return clip(await response.text(), 12000);
  }
  if (provider.id === 'firecrawl-search') {
    const response = await requireOk(await fetch('https://api.firecrawl.dev/v1/search', {
      method: 'POST',
      headers: { 'content-type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({ query, limit })
    }), provider);
    const data = await response.json();
    return clip(formatSearchItems(data.data || data.results || []));
  }
  throw new Error(`web-search provider ${provider.id} is not implemented`);
}

async function callWebRead(provider, url, options = {}) {
  const apiKey = process.env[provider.auth_env];
  if (!apiKey) {
    throw new Error(`missing environment variable ${provider.auth_env} for provider ${provider.id}`);
  }
  if (provider.id === 'jina-read') {
    const target = url.startsWith('http://') || url.startsWith('https://') ? url : `https://${url}`;
    const response = await requireOk(await fetch(`https://r.jina.ai/${target}`, {
      headers: { Authorization: `Bearer ${apiKey}` }
    }), provider);
    return clip(await response.text());
  }
  if (provider.id === 'firecrawl-scrape') {
    const response = await requireOk(await fetch('https://api.firecrawl.dev/v1/scrape', {
      method: 'POST',
      headers: { 'content-type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({ url, formats: ['markdown'] })
    }), provider);
    const data = await response.json();
    return clip((data.data && data.data.markdown) || data.markdown || '');
  }
  throw new Error(`web-read provider ${provider.id} is not implemented`);
}

async function callScholarSearch(provider, query, options = {}) {
  const limit = Math.max(1, Math.min(options.limit ?? 8, 25));
  const apiKey = process.env[provider.auth_env];
  if (!apiKey) {
    throw new Error(`missing environment variable ${provider.auth_env} for provider ${provider.id}`);
  }
  if (provider.id === 'openalex-search') {
    const params = new URLSearchParams({ search: query, 'per-page': String(limit) });
    params.set('api_key', apiKey);
    const response = await requireOk(await fetch(`https://api.openalex.org/works?${params}`, {
      headers: { accept: 'application/json' }
    }), provider);
    const data = await response.json();
    return clip(formatSearchItems((data.results || []).map(work => ({
      title: work.display_name,
      url: work.id || (work.doi ? `https://doi.org/${work.doi}` : ''),
      description: `${work.publication_year ?? ''} ${work.doi ?? ''}`.trim()
    }))));
  }
  if (provider.id === 'semantic-scholar-search') {
    const params = new URLSearchParams({ query, limit: String(limit), fields: 'title,year,externalIds,url' });
    const response = await requireOk(await fetch(`https://api.semanticscholar.org/graph/v1/paper/search?${params}`, {
      headers: { 'x-api-key': apiKey }
    }), provider);
    const data = await response.json();
    return clip(formatSearchItems((data.data || []).map(paper => ({
      title: paper.title,
      url: paper.url || (paper.externalIds && paper.externalIds.DOI ? `https://doi.org/${paper.externalIds.DOI}` : ''),
      description: String(paper.year ?? '')
    }))));
  }
  if (provider.id === 'core-search') {
    const response = await requireOk(await fetch('https://api.core.ac.uk/v3/search/works', {
      method: 'POST',
      headers: { 'content-type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({ q: query, limit })
    }), provider);
    const data = await response.json();
    return clip(formatSearchItems((data.results || []).map(work => ({
      title: work.title || (work.titles && work.titles[0]) || work.id,
      url: work.downloadUrl || work.id || '',
      description: work.abstract || ''
    }))));
  }
  if (provider.id === 'pubmed-search') {
    const searchParams = new URLSearchParams({ db: 'pubmed', term: query, retmode: 'json', retmax: String(limit) });
    searchParams.set('api_key', apiKey);
    const es = await requireOk(await fetch(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?${searchParams}`), provider);
    const searchData = await es.json();
    const ids = ((searchData.esearchresult && searchData.esearchresult.idlist) || []).slice(0, limit);
    if (ids.length === 0) {
      return 'No PubMed results.';
    }
    const summaryParams = new URLSearchParams({ db: 'pubmed', id: ids.join(','), retmode: 'json' });
    summaryParams.set('api_key', apiKey);
    const su = await requireOk(await fetch(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?${summaryParams}`), provider);
    const summaryData = await su.json();
    const items = ids.map(id => {
      const entry = (summaryData.result && summaryData.result[id]) || {};
      return {
        title: entry.title || id,
        url: `https://pubmed.ncbi.nlm.nih.gov/${id}/`,
        description: `${entry.source ?? ''} ${entry.pubdate ?? ''}`.trim()
      };
    });
    return clip(formatSearchItems(items));
  }
  if (provider.id === 'orcid-record') {
    const orcid = query.trim().replace('https://orcid.org/', '');
    if (!/^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/.test(orcid)) {
      throw new Error('orcid-record expects an ORCID iD as the query');
    }
    const response = await requireOk(await fetch(`https://pub.orcid.org/v3.0/${orcid}/record`, {
      headers: { accept: 'application/json' }
    }), provider);
    const data = await response.json();
    const name = data.person && data.person.name;
    const displayName = name
      ? [name['given-names'] && name['given-names'].value, name['family-name'] && name['family-name'].value].filter(Boolean).join(' ')
      : '';
    const works = (data['activities-summary'] && data['activities-summary'].works && data['activities-summary'].works.group) || [];
    const lines = [`# ORCID ${orcid} — ${displayName || '(no public name)'} (${works.length} works)`];
    for (const group of works.slice(0, limit)) {
      const summary = group['work-summary'] && group['work-summary'][0];
      if (summary) {
        const title = (summary.title && summary.title.title && summary.title.title.value) || '(untitled)';
        const year = summary['publication-date'] && summary['publication-date'].year && summary['publication-date'].year.value;
        lines.push(`- ${title}${year ? ` (${year})` : ''}`);
      }
    }
    return clip(lines.join('\n'));
  }
  throw new Error(`scholar-search provider ${provider.id} is not implemented`);
}

async function callRuntime(provider, task, options = {}) {
  throw new Error(`provider ${provider.id}: runtime transport is not implemented yet (registered as planned)`);
}

class ProviderAdapter {
  constructor(provider) {
    this.provider = provider;
  }
  supports(task) {
    return isSelectable(this.provider, task);
  }
  async run(task, options) {
    throw new Error('adapter run not implemented');
  }
}

class OpenAIChatAdapter extends ProviderAdapter {
  async run(task, options) {
    return callOpenAICompatible(this.provider, options.prompt, options);
  }
}

class WebSearchAdapter extends ProviderAdapter {
  async run(task, options) {
    return callWebSearch(this.provider, task.query || task.title, options);
  }
}

class WebReadAdapter extends ProviderAdapter {
  async run(task, options) {
    return callWebRead(this.provider, task.query || task.title, options);
  }
}

class ScholarSearchAdapter extends ProviderAdapter {
  async run(task, options) {
    return callScholarSearch(this.provider, task.query || task.title, options);
  }
}

class RuntimeAdapter extends ProviderAdapter {
  async run(task, options) {
    return callRuntime(this.provider, task, options);
  }
}

class CompactionAdapter {
  constructor(options = {}) {
    this.options = options;
  }
  async compact(task, provider) {
    return compactInputs(task, provider, this.options);
  }
}

const ADAPTER_FOR_TRANSPORT = {
  'openai-compat': OpenAIChatAdapter,
  'openai-chat': OpenAIChatAdapter,
  'web-search': WebSearchAdapter,
  'web-read': WebReadAdapter,
  'scholar-search': ScholarSearchAdapter,
  runtime: RuntimeAdapter
};

async function dispatchProvider(provider, task, options = {}) {
  if (provider.transport === 'planned') {
    throw new Error(`provider ${provider.id}: transport ${provider.transport} is planned, not live`);
  }
  const Adapter = ADAPTER_FOR_TRANSPORT[provider.transport];
  if (!Adapter) {
    throw new Error(`provider ${provider.id}: transport ${provider.transport} is not implemented`);
  }
  return new Adapter(provider).run(task, options);
}

function reviewSidecarPath(task, evidenceDir = EVIDENCE_DIR) {
  return path.join(evidenceDir, `${task.id}.review.json`);
}

function writeReviewRecord(task, runRecord, review, options = {}) {
  if (!task) {
    throw new Error('task is required');
  }
  if (!review || !REVIEW_STATUSES.includes(review.status) || review.status === 'pending') {
    throw new Error('review status must be accepted or rejected');
  }
  const evidenceDir = options.evidenceDir || EVIDENCE_DIR;
  const recordPath = path.join(evidenceDir, `${task.id}.run.json`);
  if (!runRecord) {
    if (!fs.existsSync(recordPath)) {
      throw new Error(`no run record for task ${task.id}; run the task first`);
    }
    runRecord = JSON.parse(fs.readFileSync(recordPath, 'utf8'));
  }
  const reviewedAt = new Date().toISOString();
  const runSha = (runRecord.review && runRecord.review.run_sha256)
    || sha256(`${runRecord.prompt_sha256}\n${runRecord.response_sha256}\n${runRecord.status}`);
  const outputSha = runRecord.response_sha256 || (runRecord.review && runRecord.review.output_sha256) || null;
  const sidecar = {
    task_id: task.id,
    status: review.status,
    reviewer: 'owner',
    reviewed_at: reviewedAt,
    notes: review.notes ?? null,
    run_sha256: runSha,
    output_sha256: outputSha
  };
  fs.writeFileSync(reviewSidecarPath(task, evidenceDir), `${JSON.stringify(sidecar, null, 2)}\n`, 'utf8');
  runRecord.review = {
    status: review.status,
    reviewer: 'owner',
    reviewed_at: reviewedAt,
    notes: sidecar.notes,
    run_sha256: runSha,
    output_sha256: outputSha
  };
  fs.writeFileSync(recordPath, `${JSON.stringify(runRecord, null, 2)}\n`, 'utf8');
  return sidecar;
}

class ReviewStore {
  constructor(options = {}) {
    this.options = options;
  }
  write(task, runRecord, review) {
    return writeReviewRecord(task, runRecord, review, this.options);
  }
  read(task) {
    const sidecar = reviewSidecarPath(task, this.options.evidenceDir);
    return fs.existsSync(sidecar) ? JSON.parse(fs.readFileSync(sidecar, 'utf8')) : null;
  }
}

function parseArgs(argv) {
  const args = {
    registry: DEFAULT_REGISTRY,
    manifest: DEFAULT_MANIFEST,
    task: null,
    provider: null,
    dryRun: false,
    live: false,
    review: false,
    status: null,
    notes: null,
    contextBudget: DEFAULT_CONTEXT_BUDGET,
    noCompact: false,
    help: false,
    secretsFile: DEFAULT_SECRETS_FILE,
    unknown: []
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help') args.help = true;
    else if (arg === '--dry-run') args.dryRun = true;
    else if (arg === '--live') args.live = true;
    else if (arg === '--no-secrets-file') args.secretsFile = null;
    else if (arg === '--no-compact') args.noCompact = true;
    else if (arg === '--review') args.review = true;
    else if (arg === '--task') args.task = argv[++i];
    else if (arg === '--provider') args.provider = argv[++i];
    else if (arg === '--registry') args.registry = argv[++i];
    else if (arg === '--manifest') args.manifest = argv[++i];
    else if (arg === '--secrets-file') args.secretsFile = argv[++i];
    else if (arg === '--context-budget') args.contextBudget = parsePositiveInt(argv[++i], '--context-budget');
    else if (arg === '--status') args.status = argv[++i];
    else if (arg === '--notes') args.notes = argv[++i];
    else args.unknown.push(arg);
  }
  if (args.help) {
    return args;
  }
  if (args.dryRun && args.live) {
    throw new Error('--dry-run and --live are mutually exclusive');
  }
  if (!args.task) {
    throw new Error('--task is required');
  }
  if (args.task === '') {
    throw new Error('--task cannot be empty');
  }
  if (args.status !== null && !args.review) {
    throw new Error('--status requires --review');
  }
  if (args.review) {
    if (args.status !== 'accepted' && args.status !== 'rejected') {
      throw new Error('--review requires --status accepted|rejected');
    }
    if (args.dryRun || args.live) {
      throw new Error('--review cannot be combined with --dry-run or --live');
    }
    if (args.unknown.length > 0) {
      throw new Error(`unknown arguments: ${args.unknown.join(', ')}`);
    }
    return args;
  }
  if (!args.provider) {
    throw new Error('--provider is required');
  }
  if (args.provider === '') {
    throw new Error('--provider cannot be empty');
  }
  if (!args.dryRun && !args.live) {
    throw new Error('select either --dry-run or --live');
  }
  if (args.unknown.length > 0) {
    throw new Error(`unknown arguments: ${args.unknown.join(', ')}`);
  }
  return args;
}

function printSummary(records) {
  for (const record of records) {
    const compaction = record.compaction && record.compaction.applied ? ' compacted' : '';
    const review = record.review ? ` review=${record.review.status}` : '';
    console.log(`${record.status} ${record.task_id} ${record.provider_id} (family=${record.provider_family} cost_rank=${record.cost_rank}${compaction})${review} -> ${record.output_path}`);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log([
      'Usage:',
      '  node tools/ai-orchestrate.js --task <id> --provider <id> (--dry-run | --live)',
      '      [--context-budget N] [--no-compact] [--secrets-file FILE | --no-secrets-file]',
      '  node tools/ai-orchestrate.js --review --task <id> --status accepted|rejected [--notes "..."]',
      '',
      `Default context budget: ${DEFAULT_CONTEXT_BUDGET} tokens (kept well below 200k-token context windows).`,
      'All outputs are advisory and are not engineering evidence until owner-reviewed.'
    ].join('\n'));
    return;
  }
  loadSecretsFile(args.secretsFile);
  const providers = loadProviderRegistry(args.registry);
  const tasks = loadTaskManifest(args.manifest);
  validateTaskManifest(tasks, providers);
  const task = tasks.find(t => t.id === args.task);
  if (!task) {
    throw new Error(`unknown task ${args.task}`);
  }
  if (args.review) {
    const sidecar = writeReviewRecord(task, null, { status: args.status, notes: args.notes });
    console.log(`review ${sidecar.status} ${task.id} -> ${path.relative(ROOT, reviewSidecarPath(task))}`);
    return;
  }
  let provider = providers.find(p => p.id === args.provider);
  if (!provider) {
    throw new Error(`unknown provider ${args.provider}`);
  }
  if (!isSelectable(provider, task)) {
    const selected = selectProvider(task, providers);
    console.error(`provider ${provider.id} is not a live route for kind ${task.kind}; using ${selected.id}`);
    provider = selected;
  }
  const record = await runTask(task, provider, {
    dryRun: args.dryRun,
    contextBudget: args.contextBudget,
    noCompact: args.noCompact,
    registry: args.registry
  });
  printSummary([record]);
}

module.exports = {
  sha256,
  containsCredential,
  readJsonFile,
  loadProviderRegistry,
  loadTaskManifest,
  validateTaskManifest,
  loadSecretsFile,
  estimateTokens,
  needsCompaction,
  compactInputs,
  selectProvider,
  isSelectable,
  buildPrompt,
  callOpenAICompatible,
  callWebSearch,
  callWebRead,
  callScholarSearch,
  callRuntime,
  dispatchProvider,
  runTask,
  writeReviewRecord,
  reviewSidecarPath,
  parseArgs,
  printSummary,
  DEFAULT_REGISTRY,
  DEFAULT_MANIFEST,
  DEFAULT_SECRETS_FILE,
  DEFAULT_CONTEXT_BUDGET,
  EVIDENCE_DIR,
  CONTEXT_DIR,
  PROVIDER_FIELDS,
  TASK_FIELDS,
  FAMILY_FOR_KIND
};

if (require.main === module) {
  main().catch(error => {
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
  });
}
