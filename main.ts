// News-image entry — Monday 23 November 2026.
//
// The entry image is entry.png beside this file. It was painted by
// generate.py (Python + Pillow) from news.json, the day's verified
// stories. This program does nothing creative: it only carries that
// finished image into the output directory, byte for byte, on every run.
//
// The PNG is inspected first — signature bytes, IHDR chunk, width,
// height and colour type must all check out. Anything else is refused,
// so a broken or wrong-sized image can never be submitted by accident.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
// /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const WANTED_WIDTH = 1024;
const WANTED_HEIGHT = 1024;
// IHDR colour types we accept: 2 = truecolour (RGB), 6 = RGB + alpha.
const WANTED_COLOURS = [2, 6];

interface PngGeometry {
  width: number;
  height: number;
  colour: number;
}

function entryBytes(): Buffer {
  const location = new URL('./entry.png', import.meta.url);
  if (!existsSync(location)) {
    throw new Error('entry.png is missing beside main.ts — cannot produce the entry image');
  }
  return readFileSync(location);
}

function inspectPng(bytes: Buffer): PngGeometry {
  if (bytes.length < 33) {
    throw new Error('entry.png is too small to be a PNG file');
  }
  if (Buffer.compare(bytes.subarray(0, 8), SIGNATURE) !== 0) {
    throw new Error('entry.png does not start with the PNG signature');
  }
  if (bytes.readUInt32BE(8) !== 13 || bytes.toString('latin1', 12, 16) !== 'IHDR') {
    throw new Error('entry.png has no IHDR chunk where one belongs');
  }
  return {
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
    colour: bytes[25],
  };
}

function abort(message: string): never {
  console.error(`error: ${message}`);
  process.exit(1);
}

function main(): void {
  let bytes: Buffer;
  let geometry: PngGeometry;
  try {
    bytes = entryBytes();
    geometry = inspectPng(bytes);
  } catch (error) {
    abort(error instanceof Error ? error.message : String(error));
  }

  if (geometry.width !== WANTED_WIDTH || geometry.height !== WANTED_HEIGHT) {
    abort(
      `entry.png is not a valid ${WANTED_WIDTH}x${WANTED_HEIGHT} PNG ` +
        `(got ${geometry.width}x${geometry.height}) — refusing to copy a broken entry image`,
    );
  }
  if (!WANTED_COLOURS.includes(geometry.colour)) {
    abort(
      `entry.png has an unexpected PNG colour type (${geometry.colour}) — ` +
        'refusing to copy a broken entry image',
    );
  }

  // An empty MAKEFUN_OUTPUT_DIR is the same as an unset one.
  const outDir = process.env.MAKEFUN_OUTPUT_DIR || '/output';
  mkdirSync(outDir, { recursive: true });
  const target = join(outDir, 'entry.png');
  writeFileSync(target, bytes);
  // Read the copy back: the entry must arrive byte for byte, or fail.
  const written = readFileSync(target);
  if (!written.equals(bytes)) {
    abort(`failed to copy entry.png to ${target} intact`);
  }
  console.log(`wrote ${target} (${bytes.length} bytes)`);
}

main();
