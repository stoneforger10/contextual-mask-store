import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';

const [address, caller, attempt, fixture, expectedState = 'READY'] = process.argv.slice(2);
if (!/^0x[0-9a-fA-F]{40}$/.test(address ?? '') || !/^0x[0-9a-fA-F]{40}$/.test(caller ?? '')
    || !['contact', 'illustration'].includes(fixture)) throw Error('ADDRESS CALLER ATTEMPT contact|illustration [STATE] required');
const sha = text => crypto.createHash('sha256').update(text).digest('hex');
const canonical = value => {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object') return '{' + Object.keys(value).sort()
    .map(key => canonical(key) + ':' + canonical(value[key])).join(',') + '}';
  return JSON.stringify(value).replace(/[\u0080-\uffff]/g, char => '\\u' + char.charCodeAt(0).toString(16).padStart(4, '0'));
};
try {
  const client = createClient({chain: studionet});
  const read = (functionName, args) => client.readContract({address, functionName, args});
  const report = await read('get_attempt', [caller, attempt]);
  assert.equal(report.state, expectedState);
  const {root, ...payload} = report;
  assert.equal(root, sha(canonical(payload)));
  if (expectedState !== 'READY') {
    assert.equal(report.output, '');
    assert.equal(report.output_hash, '');
    assert.equal(report.reason, 'HASH_MISMATCH');
    console.log(JSON.stringify({attempt, state: report.state, reason: report.reason, report_root_verified: true}));
  } else {
    const text = fs.readFileSync(`examples/${fixture}.txt`, 'utf8').replace(/\r\n/g, '\n');
    const sourceHash = sha(text);
    const artifact = await read('get_artifact', [sourceHash]);
    assert.equal(report.hash, sourceHash);
    assert.deepEqual(report.labels, fixture === 'contact' ? ['CONTACT', 'EXAMPLE'] : ['EXAMPLE', 'EXAMPLE']);
    const expectedText = fixture === 'contact' ? text.replace('editor@samplepublisher.test', '[contact-email]') : text;
    assert.equal(artifact.text, expectedText);
    assert.equal(artifact.output_hash, sha(expectedText));
    const {root: artifactRoot, ...artifactPayload} = artifact;
    assert.equal(artifactRoot, sha(canonical(artifactPayload)));
    assert.equal(await read('read_chunk', [sourceHash, artifact.output_hash, 0, 1024]), expectedText);
    console.log(JSON.stringify({attempt, state: report.state, labels: report.labels, source_hash: sourceHash,
      output_hash: artifact.output_hash, report_root_verified: true, artifact_root_verified: true, bound_chunk_verified: true}));
  }
} catch (error) {
  console.error(error.code === 'ERR_ASSERTION' ? error.message : error.shortMessage ?? 'Verification failed');
  process.exitCode = 1;
}
