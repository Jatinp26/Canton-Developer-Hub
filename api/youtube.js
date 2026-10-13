const CHANNEL_ID = "UC5Xt611-4AhcGTmlOaPlIQg";
const FEED_URL = `https://www.youtube.com/feeds/videos.xml?channel_id=${CHANNEL_ID}`;
export default async function handler(req, res) {
  const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 2, 1), 15);
  try {
    const r = await fetch(FEED_URL, { headers: { "User-Agent": "canton-developer-hub" } });
    if (!r.ok) throw new Error(`YouTube HTTP ${r.status}`);
    const items = parseFeed(await r.text()).slice(0, limit);
    if (!items.length) throw new Error("feed had no entries");
    res.setHeader("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400");
    return res.status(200).json({ items });
  } catch (e) {
    console.error(`[youtube] ${e.message}`);
    return res.status(502).json({ error: "Could not load videos", items: [] });
  }
}
function parseFeed(xml) {
  return [...xml.matchAll(/<entry>([\s\S]*?)<\/entry>/g)].map(([, e]) => {
    const id = tag(e, "yt:videoId");
    return {
      id,
      title: tag(e, "title"),
      link: id ? `https://www.youtube.com/watch?v=${id}` : "",
      date: tag(e, "published") || null,
    };
  }).filter(v => v.id && v.title);
}
function tag(block, name) {
  const m = block.match(new RegExp(`<${name}[^>]*>([\\s\\S]*?)</${name}>`));
  return m ? decode(m[1].trim()) : "";
}
function decode(s) {
  return s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'").replace(/&apos;/g, "'").replace(/&amp;/g, "&");
}
