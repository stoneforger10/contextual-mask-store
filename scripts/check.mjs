import fs from 'node:fs';
import crypto from 'node:crypto';
import dns from 'node:dns';
dns.setDefaultResultOrder('ipv4first');
async function rpc(method, params) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch('https://studio.genlayer.com/api', {method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({jsonrpc: '2.0', id: 1, method, params}), signal: AbortSignal.timeout(30000)});
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (payload.error || payload.result == null) throw Error(JSON.stringify(payload.error));
      return payload.result;
    } catch (error) { if (attempt === 2) throw error; }
  }
}
const [mode, value, expectedError] = process.argv.slice(2);
if (mode === '--source') {
  if (!/^0x[0-9a-fA-F]{40}$/.test(value ?? '')) throw Error('Address required');
  const normalize = text => text.replace(/\r\n/g, '\n').trimEnd() + '\n';
  const actual = normalize(Buffer.from(await rpc('gen_getContractCode', [value]), 'base64').toString('utf8'));
  const local = normalize(fs.readFileSync('contracts/ContextualMaskStore.py', 'utf8'));
  console.log(JSON.stringify({address: value, match: actual === local, sha256: crypto.createHash('sha256').update(actual).digest('hex')}));
  if (actual !== local) process.exitCode = 1;
} else {
  if (!['--success', '--error'].includes(mode) || !/^0x[0-9a-fA-F]{64}$/.test(value ?? '')) throw Error('--success/--error HASH required');
  let tx = await rpc('eth_getTransactionByHash', [value]);
  for (let poll = 0; tx.status !== 'FINALIZED' && poll < 15; poll++) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    tx = await rpc('eth_getTransactionByHash', [value]);
  }
  const leader = tx.consensus_data?.leader_receipt?.find(item => item.mode === 'leader');
  const raw = leader?.genvm_result?.stderr || leader?.result;
  const decoded = typeof raw !== 'string' ? '' : (/^[A-Za-z0-9+/]*={0,2}$/.test(raw) && raw.length % 4 === 0
    ? Buffer.from(raw, 'base64').toString('utf8') : raw);
  console.log(JSON.stringify({hash: value, address: tx.to_address ?? tx.to, status: tx.status, execution: leader?.execution_result, consensus: tx.result_name,
    ...(mode === '--error' ? {decoded_error: decoded} : {})}));
  if (tx.status !== 'FINALIZED' || leader?.execution_result !== (mode === '--error' ? 'ERROR' : 'SUCCESS')) process.exitCode = 1;
  if (tx.result_name !== 'MAJORITY_AGREE') process.exitCode = 1;
  if (expectedError && !decoded.includes(expectedError)) process.exitCode = 1;
}
