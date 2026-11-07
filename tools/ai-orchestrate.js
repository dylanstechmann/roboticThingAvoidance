#!/usr/bin/env node
'use strict';
// AI orchestration harness: routes narrowly scoped engineering tasks to the best-suited provider
// and records auditable, advisory evidence. Never stores credentials.
// Agent-built tooling for the owner's hobby/learning project.

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const ROOT = path.resolve(__dirname, '..');
const DEFAULT_REGISTRY = path.join(ROOT, 'derived/ai-orchestration/registry.json');
const DEFAULT_MANIFEST = path.join(ROOT, 'derived/ai-orchestration/tasks.json');
const EVIDENCE_DIR = path.join(ROOT, 'derived/ai-orchestration/evidence');

const PROVIDER_FIELDS = ['id', 'role', 'endpoint', 'auth_env', 'transport', 'model_hint'];
const TASK_FIELDS = ['id', 'kind', 'title', 'input_files', 'prompt_file', 'preferred_providers', 'output_name'];

const CREDENTIAL_PATTERNS = [
  /sk-or-v1-/i,
  /tgp_v1_/i,
  /nvapi-/i,
  /jina_/i,
  /fw_/i,
  /psk-/i,
  /nck_live_/i,
  /fc-/i,
  /omtx_/i,
  /jf_live_/i
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

function validateProvider(provider) {
  if (!provider || typeof provider !== 'object') {
    throw new Error('provider must be an object');
  }
  for (const field of PROVIDER_FIELDS) {
    if (!provider[field] || (Array.isArray(provider[field]) && provider[field].length === 0)) {
      throw new Error(`provider missing field ${field}`);
    }
  }
  if (!Array.isArray(provider.role)) {
    throw new Error(`provider ${provider.id}: role must be an array`);
  }
  if (typeof provider.endpoint !== 'string' || !/^https?:\/\//.test(provider.endpoint)) {
    throw new Error(`provider ${provider.id}: endpoint must be an http(s) URL`);
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

function selectProvider(task, providers) {
  const preferred = providers.filter(p => task.preferred_providers.includes(p.id) && p.role.includes(task.kind));
  if (preferred.length > 0) {
    return preferred[0];
  }
  const roleMatch = providers.filter(p => p.role.includes(task.kind));
  if (roleMatch.length > 0) {
    return roleMatch[0];
  }
  throw new Error(`task ${task.id}: no provider for kind ${task.kind}`);
}

function buildPrompt(task, provider) {
  const promptPath = path.join(ROOT, task.prompt_file);
  const template = fs.readFileSync(promptPath, 'utf8');
  const inputBlocks = task.input_files.map(input => {
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
  const prompt = [
    template.trim(),
    '',
    '## Input files',
    inputBlocks,
    '',
    '## Provider hint',
    `provider_id=${provider.id}`,
    `model_hint=${provider.model_hint}`,
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
    `model_hint: ${provider.model_hint}`,
    `prompt_sha256: ${sha256(prompt)}`,
    '',
    'This is a deterministic dry-run. No network request was made and no provider credentials were used.',
    '',
    'Next owner action: review this plan, then enable a live provider with the corresponding environment variable.'
  ].join('\n');
}

async function runTask(task, provider, options = { dryRun: true }) {
  if (!task || !provider) {
    throw new Error('task and provider are required');
  }
  const prompt = buildPrompt(task, provider);
  const startedAt = new Date().toISOString();
  let output;
  let status = 'success';
  try {
    output = options.dryRun ? dryRunResponse(task, provider, prompt) : await callOpenAICompatible(provider, prompt, options);
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
  const record = {
    task_id: task.id,
    provider_id: provider.id,
    model: provider.model_hint,
    started_at: startedAt,
    finished_at: finishedAt,
    status,
    prompt_sha256: sha256(prompt),
    response_sha256: sha256(output),
    input_files: task.input_files.map(input => ({ path: input, sha256: sha256(fs.readFileSync(path.join(ROOT, input), 'utf8')) })),
    output_path: path.relative(ROOT, evidencePath),
    notes: 'Agent-run; not owner-reviewed.'
  };
  fs.writeFileSync(recordPath, `${JSON.stringify(record, null, 2)}\n`, 'utf8');
  return record;
}


function parseArgs(argv) {
  const args = {
    registry: DEFAULT_REGISTRY,
    manifest: DEFAULT_MANIFEST,
    task: null,
    provider: null,
    dryRun: false,
    live: false,
    help: false,
    unknown: []
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help') args.help = true;
    else if (arg === '--dry-run') args.dryRun = true;
    else if (arg === '--live') args.live = true;
    else if (arg === '--task') args.task = argv[++i];
    else if (arg === '--provider') args.provider = argv[++i];
    else if (arg === '--registry') args.registry = argv[++i];
    else if (arg === '--manifest') args.manifest = argv[++i];
    else args.unknown.push(arg);
  }
  if (args.dryRun && args.live) {
    throw new Error('--dry-run and --live are mutually exclusive');
  }
  if (args.task === undefined) {
    throw new Error('--task is required');
  }
  if (args.provider === undefined) {
    throw new Error('--provider is required');
  }
  if (args.task === '') {
    throw new Error('--task cannot be empty');
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
    console.log(`${record.status} ${record.task_id} ${record.provider_id} -> ${record.output_path}`);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log('Usage: node tools/ai-orchestrate.js --task <id> --provider <id> (--dry-run | --live)');
    return;
  }
  const providers = loadProviderRegistry(args.registry);
  const tasks = loadTaskManifest(args.manifest);
  const task = tasks.find(t => t.id === args.task);
  if (!task) {
    throw new Error(`unknown task ${args.task}`);
  }
  let provider = providers.find(p => p.id === args.provider);
  if (!provider) {
    throw new Error(`unknown provider ${args.provider}`);
  }
  if (!provider.role.includes(task.kind)) {
    const selected = selectProvider(task, providers);
    console.error(`provider ${provider.id} does not support kind ${task.kind}; using ${selected.id}`);
    provider = selected;
  }
  const record = await runTask(task, provider, { dryRun: args.dryRun });
  printSummary([record]);
}

module.exports = {
  sha256,
  containsCredential,
  loadProviderRegistry,
  loadTaskManifest,
  selectProvider,
  buildPrompt,
  runTask,
  parseArgs,
  printSummary,
  DEFAULT_REGISTRY,
  DEFAULT_MANIFEST,
  EVIDENCE_DIR,
  PROVIDER_FIELDS,
  TASK_FIELDS
};

if (require.main === module) {
  main().catch(error => {
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
  });
}
