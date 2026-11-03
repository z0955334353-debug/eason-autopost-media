import { session, json, threads } from "../../lib/threads.js";

const BLOCK = /(https?:\/\/|www\.|line\.me|lin\.ee|私訊|加LINE|加line|加賴)/i;

// 在搜尋到的公開貼文底下回覆（每次都是使用者親自按下送出）
export async function onRequestPost({ request, env }) {
  const s = await session(request, env);
  if (!s) return json({ error: "請先登入" }, 401);
  const { postId, text } = await request.json().catch(() => ({}));
  const msg = (text || "").trim();
  if (!postId || !/^\d+$/.test(String(postId))) return json({ error: "貼文編號不正確" }, 400);
  if (!msg || msg.length > 500) return json({ error: "留言要 1～500 字" }, 400);
  if (BLOCK.test(msg)) return json({ error: "留言不能含連結、「私訊」「加LINE」，容易被判成垃圾留言" }, 400);
  try {
    const c = await threads("POST", "me/threads", { media_type: "TEXT", text: msg, reply_to_id: String(postId) }, s.t);
    await new Promise((r) => setTimeout(r, 2000));
    const p = await threads("POST", "me/threads_publish", { creation_id: c.id }, s.t);
    let permalink = "";
    try {
      permalink = (await threads("GET", p.id, { fields: "permalink" }, s.t)).permalink || "";
    } catch {}
    return json({ ok: true, id: p.id, permalink });
  } catch (e) {
    return json({ error: e.message }, 502);
  }
}
