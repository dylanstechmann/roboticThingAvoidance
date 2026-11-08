'use strict';
// Offline tests for the JSON task-object validator (the documented follow-up
// from the 2026-11-07 study pack). No network calls are made: the validator is
// pure and the real registry/manifest are read-only fixtures.

const { test } = require('node:test');
const assert = require('node:assert/strict');

const {
  loadProviderRegistry,
  loadTaskManifest,
  validateTaskManifest,
  DEFAULT_REGISTRY,
  DEFAULT_MANIFEST
} = require('../tools/ai-orchestrate.js');

function realFixtures() {
  return {
    providers: loadProviderRegistry(DEFAULT_REGISTRY),
    tasks: loadTaskManifest(DEFAULT_MANIFEST)
  };
}

// A well-formed task object shaped like the real manifest entries.
function baseTask() {
  return {
    id: 'unit-task',
    kind: 'search',
    title: 'Unit test task',
    input_files: ['RULES-AND-SOURCES.md'],
    prompt_file: 'prompts/rules-update-scan.md',
    preferred_providers: ['exa-search'],
    output_name: 'unit-task.md',
    query: 'unit query',
    owner_review: false
  };
}

test('the real manifest passes the task-object validator', () => {
  const { providers, tasks } = realFixtures();
  assert.equal(validateTaskManifest(tasks, providers), tasks);
});

test('unknown preferred provider id is rejected', () => {
  const { providers } = realFixtures();
  const task = baseTask();
  task.preferred_providers = ['exa-search', 'no-such-provider'];
  assert.throws(() => validateTaskManifest([task], providers), /unknown preferred provider no-such-provider/);
});

test('preferred providers without a live route for the kind are rejected', () => {
  const { providers } = realFixtures();
  const task = baseTask();
  task.preferred_providers = ['openrouter-general']; // chat family; task kind is search
  assert.throws(() => validateTaskManifest([task], providers), /no preferred provider is a live route for kind search/);
});

test('planned transports never count as a live route', () => {
  const { providers } = realFixtures();
  const task = baseTask();
  task.kind = 'planning';
  delete task.query;
  task.preferred_providers = ['omtx-general'];
  assert.throws(() => validateTaskManifest([task], providers), /no preferred provider is a live route for kind planning/);
});

test('output_name must be a safe .md file name', () => {
  const { providers } = realFixtures();
  for (const bad of ['../evil.md', 'sub/dir.md', 'notes.txt', '.hidden.md', 'a..md']) {
    const task = baseTask();
    task.output_name = bad;
    assert.throws(() => validateTaskManifest([task], providers), /output_name/, `output_name ${bad} should be rejected`);
  }
});

test('search-family kinds require a non-empty query', () => {
  const { providers } = realFixtures();
  const missing = baseTask();
  delete missing.query;
  assert.throws(() => validateTaskManifest([missing], providers), /kind search requires a non-empty query/);
  const blank = baseTask();
  blank.query = '   ';
  assert.throws(() => validateTaskManifest([blank], providers), /requires a non-empty query/);
});

test('chat-family kinds do not require a query', () => {
  const { providers } = realFixtures();
  const task = baseTask();
  task.kind = 'planning';
  delete task.query;
  task.preferred_providers = ['openrouter-general'];
  validateTaskManifest([task], providers); // must not throw
});

test('owner_review must be a boolean when present', () => {
  const { providers } = realFixtures();
  const task = baseTask();
  task.owner_review = 'yes';
  assert.throws(() => validateTaskManifest([task], providers), /owner_review must be a boolean/);
});

test('empty or blank titles are rejected', () => {
  const { providers } = realFixtures();
  const blank = baseTask();
  blank.title = '   ';
  assert.throws(() => validateTaskManifest([blank], providers), /title must be a non-empty string/);
});

test('prompt_file and input_files must stay inside the repository', () => {
  const { providers } = realFixtures();
  const absolute = baseTask();
  absolute.prompt_file = '/etc/passwd';
  assert.throws(() => validateTaskManifest([absolute], providers), /prompt_file must be a relative path/);
  const traversal = baseTask();
  traversal.input_files = ['../outside.md'];
  assert.throws(() => validateTaskManifest([traversal], providers), /must be a relative path inside the repository/);
});

test('empty preferred_providers is rejected', () => {
  const { providers } = realFixtures();
  const task = baseTask();
  task.preferred_providers = [];
  assert.throws(() => validateTaskManifest([task], providers), /preferred_providers must be a non-empty array/);
});
