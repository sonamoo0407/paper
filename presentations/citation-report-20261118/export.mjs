import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';
import { buildReport } from './build-report.mjs';

const directory = path.dirname(fileURLToPath(import.meta.url));
const output = path.resolve(process.argv[2] || path.join(directory, 'research-report-regenerated.pptx'));
try {
  await fs.access(output);
  throw new Error(`Choose a new output path. File already exists: ${output}`);
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
await fs.mkdir(path.dirname(output), { recursive: true });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
await buildReport(presentation, { nativeImages: true });
await (await PresentationFile.exportPptx(presentation)).save(output);
console.log(`Exported ${presentation.slides.items.length} slides to ${output}`);
