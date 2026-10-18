import assert from "node:assert/strict";
import { test } from "node:test";

import { catalogStats, classifyTech, esc, hay, installCmd, kb, mb } from "../catalog-lib.js";

test("esc escapes the characters that would break the markup", () => {
  assert.equal(esc(`<a href="x">&</a>`), "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;");
  assert.equal(esc(null), "");
  assert.equal(esc(undefined), "");
  assert.equal(esc(5), "5");
});

test("mb and kb format sizes and show a dash when there is none", () => {
  assert.equal(mb(32_800_000), "32.8 Mb");
  assert.equal(mb(0), "–");
  assert.equal(kb(1_169_298), "1.17 Mb");
  assert.equal(kb(694_934), "695 kb");
  assert.equal(kb(undefined), "–");
});

test("classifyTech sorts sequencing technologies into categories", () => {
  assert.equal(classifyTech(""), "Unknown");
  assert.equal(classifyTech("Illumina HiSeq 2500"), "Illumina");
  assert.equal(classifyTech("PacBio RS II"), "PacBio");
  assert.equal(classifyTech("Oxford Nanopore MinION"), "Oxford Nanopore");
  assert.equal(classifyTech("454 GS FLX"), "Legacy (454/Ion/SOLiD)");
  assert.equal(classifyTech("Illumina; Nanopore"), "Hybrid");
  assert.equal(classifyTech("something else"), "Other");
});

test("hay gathers what a search term is matched against, lowercased", () => {
  const g = { identifier: "TriTrypDB-71_LmajorFriedlin", species: "Leishmania major", strain: "Friedlin", aliases: ["LmjF"] };
  const text = hay(g);
  assert.ok(text.includes("tritrypdb-71_lmajorfriedlin"));
  assert.ok(text.includes("leishmania major"));
  assert.ok(text.includes("lmjf"));
});

test("installCmd names the alias when the catalog has one", () => {
  assert.equal(installCmd({ identifier: "GCA_1.1" }), "leishref install GCA_1.1");
  assert.equal(installCmd({ identifier: "GCA_1.1", aliases: ["Lmajor"] }), "leishref install GCA_1.1 --alias Lmajor");
});

test("catalogStats counts genomes, species, chromosome-level entries and the origins", () => {
  const genomes = [
    { group: "ncbi", species: "Leishmania major", assembly_level: "Complete Genome" },
    { group: "ncbi", species: "Leishmania major", assembly_level: "Scaffold" },
    { group: "tritrypdb", species: "Leishmania major", assembly_level: "Chromosome" },
    { group: "tritrypdb", species: "Leishmania tropica", assembly_level: "Chromosome" },
    { group: "custom", species: "Leishmania tropica", assembly_level: "Scaffold" },
    { group: "scaffolds" },
  ];
  assert.deepEqual(catalogStats(genomes), {
    genomes: 6,
    species: 2,
    chromosomeLevel: 3,
    origins: [["NCBI", 2], ["TriTrypDB", 2], ["others", 2]],
  });
});

test("catalogStats of an empty catalog is all zeros", () => {
  const st = catalogStats([]);
  assert.equal(st.genomes, 0);
  assert.deepEqual(st.origins, [["NCBI", 0], ["TriTrypDB", 0], ["others", 0]]);
});
