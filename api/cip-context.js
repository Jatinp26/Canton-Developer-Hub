const ORIGIN = "https://lists.sync.global";
const GROUPS = ["cip-announce", "cip-discuss"];
const MAX_MENTIONS = 10;
export default async function handler(req, res) {
  const num = String(req.query.cip || "").replace(/\D/g, "").replace(/^0+/, "");
  if (!num) return res.status(400).json({ error: "cip query param required, e.g. ?cip=103" });
  const padded = num.padStart(4, "0");
  const cipId = `CIP-${padded}`;
  const [doc, mentions] = await Promise.all([
    fetchCipDoc(padded).catch(e => ({ found: false, error: e.message })),
    fetchMentions(num, padded).catch(e => { console.warn(`[cip-context] mentions: ${e.message}`); return []; }),
  ]);
  res.setHeader("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400");
  return res.status(200).json({ cip: cipId, ...doc, mentions });
}
async function fetchCipDoc(padded) {
  const url = `https://raw.githubusercontent.com/canton-foundation/cips/main/cip-${padded}/cip-${padded}.md`;
  const r = await fetch(url);
  if (r.status === 404) return { found: false };
  if (!r.ok) throw new Error(`GitHub HTTP ${r.status}`);
  const md = await r.text();
  const header = {};
  const pre = md.match(/<pre>([\s\S]*?)<\/pre>/i);
  if (pre) {
    for (const line of pre[1].split("\n")) {
      const m = line.match(/^\s*([A-Za-z-]+):\s*(.+?)\s*$/);
      if (m) header[m[1].toLowerCase()] = m[2];
    }
  }
  const section = name => {
    const m = md.match(new RegExp(`^##\\s+${name}\\s*\\n([\\s\\S]*?)(?=^##\\s)`, "im"));
    return m ? clean(m[1]) : "";
  };
  const headings = [...md.matchAll(/^##\s+(.+)$/gm)].map(m => m[1].trim()).slice(0, 15);
  return {
    found: true,
    title: header.title || (md.match(/^#\s+(.+)$/m)?.[1] ?? ""),
    status: header.status || null,
    type: header.type || null,
    created: header.created || null,
    approved: header.approved || null,
    postHistory: header["post-history"] || null,
    url: `https://github.com/canton-foundation/cips/blob/main/cip-${padded}/cip-${padded}.md`,
    abstract: section("Abstract").slice(0, 1800),
    motivation: section("Motivation").slice(0, 700),
    headings,
  };
}
async function fetchMentions(num, padded) {
  const key = process.env.GROUPS_IO_API_KEY;
  let all = [];
  if (key) {
    try {
      const queries = [`CIP-${padded}`, `CIP-${num}`];
      const results = await Promise.all(
        GROUPS.flatMap(g => queries.map(q => searchGroup(g, q, key)))
      );
      all = results.flat();
    } catch (e) {
      console.warn(`[cip-context] api search failed, using rss: ${e.message}`);
    }
  }
  if (!all.length) all = await rssMentions(num, padded);
  const seen = new Set();
  return all
    .filter(m => { const k = m.list + "|" + m.subject + "|" + m.date; if (seen.has(k)) return false; seen.add(k); return true; })
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .slice(0, MAX_MENTIONS);
}
async function searchGroup(group, q, key) {
  const url = `${ORIGIN}/api/v1/searcharchives?group_name=${encodeURIComponent(group)}&q=${encodeURIComponent(q)}&limit=10`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (!r.ok) throw new Error(`${group} HTTP ${r.status}`);
  const data = await r.json();
  if (data.object === "error" || !Array.isArray(data.data)) throw new Error(data.type || "unexpected response");
  return data.data.map(m => ({
    list: group,
    subject: m.subject || "",
    date: toISO(m.created),
    snippet: clean(m.snippet || m.summary || m.body || "").slice(0, 400),
    link: m.topic_id ? `${ORIGIN}/g/${group}/topic/${m.topic_id}` : `${ORIGIN}/g/${group}`,
  }));
}
async function rssMentions(num, padded) {
  const re = new RegExp(`CIP[-\\s]?0*${num}\\b`, "i");
  const out = [];
  for (const group of GROUPS) {
    try {
      const r = await fetch(`${ORIGIN}/g/${group}/rss`, { headers: { "User-Agent": "canton-developer-hub" } });
      if (!r.ok) continue;
      const xml = await r.text();
      for (const [block] of xml.matchAll(/<item[\s>][\s\S]*?<\/item>/gi)) {
        const title = pick(block, "title"), desc = pick(block, "description");
        if (!re.test(title) && !re.test(desc)) continue;
        out.push({ list: group, subject: title, date: toISO(pick(block, "pubDate")), snippet: clean(desc).slice(0, 400), link: pick(block, "link") });
      }
    } catch (e) {}
  }
  return out;
}
function pick(block, tag) {
  const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, "i"));
  return m ? decode(m[1].replace(/^<!\[CDATA\[|\]\]>$/g, "").trim()) : "";
}
function decode(s) {
  return s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&");
}
function clean(s) {
  return decode(String(s))
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_`>#]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
function toISO(v) {
  if (!v) return null;
  const d = new Date(typeof v === "number" ? v * 1000 : v);
  return isNaN(d) ? null : d.toISOString().slice(0, 10);
}
