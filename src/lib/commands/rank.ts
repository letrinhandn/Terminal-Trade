/**
 * Command ranking
 * (token-prefix tiers studied from CommandMatch / CommandRank - no AGPL code).
 */

export function words(text: string): string[] {
  const out: string[] = [];
  let cur = "";
  for (const c of text) {
    if (/[a-zA-Z0-9]/.test(c)) cur += c.toLowerCase();
    else if (cur) {
      out.push(cur);
      cur = "";
    }
  }
  if (cur) out.push(cur);
  return out;
}

function prefixesInOrder(query: string[], field: string[]): boolean {
  let at = 0;
  for (const q of query) {
    let found = false;
    while (at < field.length) {
      if (field[at++].startsWith(q)) {
        found = true;
        break;
      }
    }
    if (!found) return false;
  }
  return true;
}

function prefixesAnywhere(query: string[], field: string[]): boolean {
  return query.every((q) => field.some((w) => w.startsWith(q)));
}

export type RankFields = {
  title: string;
  aliases: string[];
  keywords: string[];
  description?: string;
  id?: string;
};

/** Higher = better. 0 = no match. */
export function scoreMatch(queryRaw: string, fields: RankFields): number {
  const q = queryRaw.trim().toLowerCase();
  const qWords = words(q);
  if (!q || !qWords.length) return 0;

  const qNorm = qWords.join(" ");
  let best = 0;
  const take = (s: number) => {
    best = Math.max(best, s);
  };

  for (const a of fields.aliases) {
    if (a.toLowerCase() === q) take(100);
  }

  const nameWords = words(fields.title);
  const nameNorm = nameWords.join(" ");
  if (nameNorm === qNorm || nameWords.join("") === qWords.join("")) take(95);
  else if (nameNorm.startsWith(qNorm)) take(90);
  else if (prefixesInOrder(qWords, nameWords)) take(85);

  for (const a of fields.aliases) {
    if (a.toLowerCase().startsWith(q)) take(80);
  }

  let titleWords = [...nameWords, ...words(fields.id || "")];
  for (const a of fields.aliases) titleWords = titleWords.concat(words(a));
  if (prefixesAnywhere(qWords, titleWords)) take(75);

  if (fields.title.toLowerCase().includes(q)) take(70);
  for (const a of fields.aliases) {
    if (a.toLowerCase().includes(q)) take(60);
  }

  if (best < 45) {
    let all = [...titleWords];
    for (const k of fields.keywords) all = all.concat(words(k));
    all = all.concat(words(fields.description || ""));
    if (prefixesAnywhere(qWords, all)) take(45);
  }
  if ((fields.description || "").toLowerCase().includes(q)) take(40);
  for (const k of fields.keywords) {
    if (k.toLowerCase().includes(q)) take(30);
  }
  return best;
}
