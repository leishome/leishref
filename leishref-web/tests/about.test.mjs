import assert from "node:assert/strict";
import { test } from "node:test";

import { summarize } from "../about.js";

const genomes = [
  { source: "RefSeq", assembly_level: "Chromosome", species: "Leishmania major", files: { fasta: "a.fna", gff: "a.gff" } },
  { source: "RefSeq", assembly_level: "Scaffold", species: "Leishmania major", files: { fasta: "b.fna" } },
  { source: "TriTrypDB", assembly_level: "Chromosome", species: "Leishmania tropica", files: { fasta: "c.fasta", gff: "c.gff" } },
  { source: "Custom", species: "Leishmania tropica" },
  {},
];

test("summarize counts genomes, species and entries with a GFF", () => {
  const s = summarize(genomes);
  assert.equal(s.genomes, 5);
  assert.equal(s.species, 3); // major, tropica, unknown
  assert.equal(s.withGff, 2);
});

test("summarize groups by source and level, largest first, with 'unknown' for a missing value", () => {
  const s = summarize(genomes);
  assert.deepEqual(s.bySource, [["RefSeq", 2], ["Custom", 1], ["TriTrypDB", 1], ["unknown", 1]]);
  assert.deepEqual(s.byLevel, [["Chromosome", 2], ["unknown", 2], ["Scaffold", 1]]);
});

test("summarize lists species with their genome and GFF counts", () => {
  const s = summarize(genomes);
  assert.deepEqual(s.perSpecies, [
    { species: "Leishmania major", genomes: 2, gff: 1 },
    { species: "Leishmania tropica", genomes: 2, gff: 1 },
    { species: "unknown", genomes: 1, gff: 0 },
  ]);
});

test("summarize of an empty catalog is empty", () => {
  const s = summarize([]);
  assert.equal(s.genomes, 0);
  assert.deepEqual(s.perSpecies, []);
});
