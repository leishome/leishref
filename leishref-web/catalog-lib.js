// Pure helpers of the catalog page, kept free of the DOM so that they can be tested with `node --test`.

export const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const mb = (b) => (b ? (b / 1e6).toFixed(1) + " Mb" : "–");
export const kb = (b) => (b ? (b >= 1e6 ? (b / 1e6).toFixed(2) + " Mb" : (b / 1e3).toFixed(0) + " kb") : "–");

export function classifyTech(s) {
  if (!s) return "Unknown";
  const t = s.toLowerCase();
  const f = [/illumina|hiseq|miseq|novaseq|nextseq|gaiix?/, /nanopore|minion|gridion|promethion/, /pacbio|rs ?ii|sequel/, /454|ion ?torrent|solid/].map((r) => r.test(t));
  if (f.filter(Boolean).length > 1) return "Hybrid";
  return f[0] ? "Illumina" : f[1] ? "Oxford Nanopore" : f[2] ? "PacBio" : f[3] ? "Legacy (454/Ion/SOLiD)" : "Other";
}

export const hay = (g) =>
  [g.identifier, g.accession, g.species, g.strain, g.source, g.assembly_level, g.taxon_id, g.notes, g.tech, g.techCat, ...(g.aliases || [])]
    .join(" ").toLowerCase();

export function installCmd(g) {
  const alias = (g.aliases || [])[0];
  return `leishref install ${g.identifier}` + (alias ? ` --alias ${alias}` : "");
}

// Numbers for the statistics boxes. The same genome can be in the catalog under several origins
// (e.g. NCBI and TriTrypDB), so the last box splits the entries by origin.
export function catalogStats(genomes) {
  const n = (group) => genomes.filter((g) => g.group === group).length;
  const origins = [["NCBI", n("ncbi")], ["TriTrypDB", n("tritrypdb")]];
  origins.push(["others", genomes.length - origins[0][1] - origins[1][1]]);
  return {
    genomes: genomes.length,
    species: new Set(genomes.map((g) => g.species).filter(Boolean)).size,
    chromosomeLevel: genomes.filter((g) => ["Complete Genome", "Chromosome"].includes(g.assembly_level)).length,
    origins,
  };
}
