// News-image entry (Node, standard library only) — Monday 23 November 2026.
//
// The entry image is entry.png beside this file, drawn by generate.py
// (Python + Pillow) from news.json — the day's verified stories.
// This program only carries it to the output directory. It writes the
// same bytes on every run.
//
// Before copying it checks the file really is a 1024x1024 PNG (magic
// bytes plus the IHDR width and height) and refuses to copy anything
// else, so a broken or wrong-sized image can never be submitted by
// accident.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
// /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

function fail(message) {
  console.error(`error: ${message}`);
  process.exit(1);
}

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const entryPath = new URL('./entry.png', import.meta.url);

let png;
try {
  png = readFileSync(entryPath);
} catch {
  fail('entry.png is missing beside main.ts — cannot produce the entry image');
}

const MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
// The PNG signature: the first eight bytes of every PNG file.

const looksLikePng =
  png.length >= 33 &&
  png.subarray(0, 8).equals(MAGIC) &&
  png.readUInt32BE(8) === 13 && // IHDR chunk length
  png.subarray(12, 16).toString('latin1') === 'IHDR';

const width = looksLikePng ? png.readUInt32BE(16) : 0;
const height = looksLikePng ? png.readUInt32BE(20) : 0;

if (!looksLikePng || width !== 1024 || height !== 1024) {
  fail(
    `entry.png is not a valid 1024x1024 PNG (got ${width}x${height}) — ` +
      'refusing to copy a broken entry image',
  );
}

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'entry.png'), png);
