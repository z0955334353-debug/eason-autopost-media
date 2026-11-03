import { session, json, threads } from "../../lib/threads.js";

// 關鍵字搜尋公開貼文（需要 threads_keyword_search 權限）
export async function onRequestGet({ request, env }) {
  const s = await session(request, env);
  if (!s) return json({ error: "請先登入" }, 401);
  const q = (new URL(request.url).searchParams.get("q") || "").trim().slice(0, 50);
  const type = new URL(request.url).searchParams.get("type") === "TOP" ? "TOP" : "RECENT";
  if (!q) return json({ error: "請輸入關鍵字" }, 400);
  try {
    const d = await threads("GET", "keyword_search", {
      q,
      search_type: type,
      fields: "id,text,permalink,timestamp,username,has_replies,media_type",
    }, s.t);
    const items = (d.data || []).map((p) => ({ ...p, own: p.username === s.u }));
    return json({ items });
  } catch (e) {
    return json({ error: e.message }, 502);
  }
}
