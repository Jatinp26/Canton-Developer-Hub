const ORIGIN = "https://lists.sync.global";
const GROUPS = { announce: "cip-announce", discuss: "cip-discuss" };

export default async function handler(req, res) {
  const group = GROUPS[req.query.list];
  if (!group) return res.status(400).json({ error: "list must be 'announce' or 'discuss'" });
  const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 3, 1), 10);
  let items = [], source = "api", apiError = null;
  try {
    items = await fromApi(group, limit);
  } catch (e) {
    apiError = e.message;
    source = "rss";
    try {
      items = await fromRss(group, limit);
    } catch (e2) {
      console.error(`[cips] ${group} api: ${apiError} | rss: ${e2.message}`);
      return res.status(502).json({ error: "Could not load CIP feed", items: [] });
    }
  }
  if (apiError) console.warn(`[cips] ${group} api failed, served rss: ${apiError}`);
  res.setHeader("Cache-Control", "s-maxage=900, stale-while-revalidate=3600");
  return res.status(200).json({ source, items });
}
async function fromApi(group, limit) {
  const key = process.env.GROUPS_IO_API_KEY;
  if (!key) throw new Error("GROUPS_IO_API_KEY not set");
  const url = `${ORIGIN}/api/v1/gettopics?group_name=${encodeURIComponent(group)}&limit=${limit}`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const data = await r.json();
  if (data.object === "error" || !Array.isArray(data.data)) throw new Error(data.type || "unexpected response");
  return data.data.slice(0, limit).map(t => ({
    title: t.subject || "",
    link: `${ORIGIN}/g/${group}/topic/${t.id}`,
    date: t.most_recent_message || t.updated || t.created || null,
  }));
}
async function fromRss(group, limit) {
  const r = await fetch(`${ORIGIN}/g/${group}/rss`, { headers: { "User-Agent": "canton-developer-hub" } });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const xml = await r.text();
  const pick = (block, tag) => {
    const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, "i"));
    return m ? decode(m[1].replace(/^<!\[CDATA\[|\]\]>$/g, "").trim()) : "";
  };
  const items = [...xml.matchAll(/<item[\s>][\s\S]*?<\/item>/gi)].map(([block]) => ({
    title: pick(block, "title"),
    link: pick(block, "link"),
    date: pick(block, "pubDate") || null,
  }));
  const seen = new Set();
  return items.filter(i => {
    const k = i.title.replace(/^re:\s*/i, "").toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  }).slice(0, limit);
}
function decode(s) {
  return s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'").replace(/&amp;/g, "&");
}
