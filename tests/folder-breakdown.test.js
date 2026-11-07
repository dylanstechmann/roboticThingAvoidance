'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
function toolFiles(dir) {
  return fs.readdirSync(dir, {withFileTypes: true}).flatMap(entry => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return entry.name === '__pycache__' ? [] : toolFiles(full);
    return entry.isFile() && /\.(js|py)$/.test(entry.name) ? [path.relative(root, full).replaceAll(path.sep, '/')] : [];
  });
}
test('folder breakdown covers every tool exactly once with real tests or explicit gaps', () => {
  const actual = toolFiles(path.join(root, 'tools')).sort();
  const lines = fs.readFileSync(path.join(root, 'docs/folder-breakdown.md'), 'utf8').split('\n')
    .filter(line => line.startsWith('| `tools'));
  const seen = new Set();
  for (const line of lines) {
    const columns = line.split('|').slice(1, -1).map(v => v.trim());
    assert.equal(columns.length, 5, `five columns: ${line}`);
    const folder = columns[0].replaceAll('`', ''), tool = columns[1].replaceAll('`', '');
    const full = `${folder}${tool}`, purpose = columns[2], goal = columns[3], gap = columns[4];
    assert.ok(fs.existsSync(path.join(root, full)), `listed tool exists: ${full}`);
    assert.ok(!seen.has(full), `duplicate row ${full}`); seen.add(full);
    assert.ok(purpose.length > 0, `purpose required: ${full}`);
    if (goal === 'GAP') assert.ok(gap && gap !== '—', `GAP reason required: ${full}`);
    else {
      const refs = [...goal.matchAll(/`([^`]+)`/g)].map(m => m[1]);
      assert.ok(refs.length > 0, `goal-test path required: ${full}`);
      for (const ref of refs) {
        assert.ok(/^(tools|tests|software|firmware)\//.test(ref), `goal-test path scope: ${full}: ${ref}`);
        assert.ok(fs.existsSync(path.join(root, ref)), `goal test exists: ${full}: ${ref}`);
      }
    }
  }
  assert.deepEqual([...seen].sort(), actual, 'live tool tree and inventory agree');
});
