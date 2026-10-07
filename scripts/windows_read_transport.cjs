// Optional Windows HTTPS fallback for public, READ-ONLY StudioNet RPC requests.
// Never intercept or retry signing/broadcast methods; never read wallet files.
const {execFile} = require('node:child_process');
const reads = new Set(['eth_chainId', 'eth_getTransactionCount', 'eth_getTransactionByHash',
  'eth_getTransactionReceipt', 'gen_call', 'gen_getContractCode', 'gen_getContractSchema', 'eth_getBalance']);
const original = globalThis.fetch;
globalThis.fetch = async (url, options) => {
  let rpc;
  try { rpc = JSON.parse(options?.body ?? '{}'); } catch {}
  const target = new URL(String(url));
  if (process.platform !== 'win32' || target.origin !== 'https://studio.genlayer.com'
      || target.pathname !== '/api' || !reads.has(rpc?.method)) return original(url, options);
  const encodedBody = Buffer.from(JSON.stringify(rpc), 'utf8').toString('base64');
  const script = `$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); `
    + `$body=[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('${encodedBody}')); `
    + `$r=Invoke-WebRequest -UseBasicParsing -Uri 'https://studio.genlayer.com/api' -Method Post `
    + `-ContentType 'application/json' -Body $body -TimeoutSec 25; [Console]::Write($r.Content)`;
  const encodedScript = Buffer.from(script, 'utf16le').toString('base64');
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const body = await new Promise((resolve, reject) => execFile('pwsh.exe',
        ['-NoProfile', '-NonInteractive', '-EncodedCommand', encodedScript],
        {windowsHide: true, encoding: 'utf8', timeout: 30000, maxBuffer: 10485760},
        (error, stdout) => error ? reject(Error(`Windows read transport failed (${error.code})`)) : resolve(stdout)));
      JSON.parse(body);
      return new Response(body, {status: 200, headers: {'content-type': 'application/json'}});
    } catch (error) { if (attempt === 2) throw error; }
  }
};
