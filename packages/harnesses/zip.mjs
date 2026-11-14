// Small, uncompressed UTF-8 ZIP writer. No dependency, telemetry or network.
const encoder = new TextEncoder();
function crc32(data) {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let k = 0; k < 8; k++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}
function header(size, values) {
  const result = new Uint8Array(size), view = new DataView(result.buffer);
  for (const [offset, value, width] of values) view[width === 2 ? 'setUint16' : 'setUint32'](offset, value, true);
  return result;
}
function join(chunks) {
  const out = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0));
  let i = 0; for (const chunk of chunks) { out.set(chunk, i); i += chunk.length; }
  return out;
}
export function zipFiles(files) {
  if (!Array.isArray(files) || !files.length || files.length > 32) throw Error('Invalid export file count.');
  const local = [], central = [], seen = new Set(); let offset = 0;
  for (const {name, text} of files) {
    if (typeof name !== 'string' || !/^[A-Za-z0-9_.\/-]+$/.test(name) || name.startsWith('/') ||
        name.split('/').some(p => !p || p === '.' || p === '..') || seen.has(name) || typeof text !== 'string')
      throw Error('Invalid ZIP entry.');
    seen.add(name);
    const n = encoder.encode(name), data = encoder.encode(text), crc = crc32(data);
    if (data.length > 2000000) throw Error('Export file is too large.');
    const l = header(30, [[0,0x04034b50,4],[4,20,2],[6,0x800,2],[12,0x21,2],
      [14,crc,4],[18,data.length,4],[22,data.length,4],[26,n.length,2]]);
    local.push(l,n,data);
    central.push(header(46, [[0,0x02014b50,4],[4,20,2],[6,20,2],[8,0x800,2],[14,0x21,2],
      [16,crc,4],[20,data.length,4],[24,data.length,4],[28,n.length,2],[42,offset,4]]),n);
    offset += l.length + n.length + data.length;
  }
  const directory = join(central);
  return join([...local, directory, header(22, [[0,0x06054b50,4],[8,files.length,2],
    [10,files.length,2],[12,directory.length,4],[16,offset,4]])]);
}
