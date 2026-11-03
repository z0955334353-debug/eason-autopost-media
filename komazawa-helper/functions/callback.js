import { APP_ID, redirectUri, readCookie, setSession, cookie } from "../lib/threads.js";

function fail(msg) {
  return new Response(`<meta charset="utf-8"><p style="font-family:sans-serif;padding:24px">登入失敗：${msg}</p><p style="font-family:sans-serif;padding:0 24px"><a href="/">回首頁</a></p>`, {
    status: 400,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  if (!code) return fail(url.searchParams.get("error_description") || "沒有取得授權碼");
  if (!state || state !== readCookie(request, "kz_state")) return fail("驗證碼不符，請重新登入");
  if (!env.THREADS_APP_SECRET) return fail("網站還沒設定 THREADS_APP_SECRET");

  // 1. 授權碼換短效權杖
  const r1 = await fetch("https://graph.threads.net/oauth/access_token", {
    method: "POST",
    body: new URLSearchParams({
      client_id: APP_ID,
      client_secret: env.THREADS_APP_SECRET,
      grant_type: "authorization_code",
      redirect_uri: redirectUri(request),
      code: code.replace(/#_$/, ""),
    }),
  });
  const d1 = await r1.json();
  if (!d1.access_token) return fail((d1.error && d1.error.message) || d1.error_message || "換權杖失敗");

  // 2. 換成 60 天長效權杖
  const u2 = new URL("https://graph.threads.net/access_token");
  u2.searchParams.set("grant_type", "th_exchange_token");
  u2.searchParams.set("client_secret", env.THREADS_APP_SECRET);
  u2.searchParams.set("access_token", d1.access_token);
  const d2 = await (await fetch(u2)).json();
  const token = d2.access_token || d1.access_token;

  // 3. 取得帳號名稱
  const me = await (await fetch(`https://graph.threads.net/v1.0/me?fields=id,username&access_token=${encodeURIComponent(token)}`)).json();

  const headers = new Headers({ Location: "/" });
  headers.append("Set-Cookie", await setSession(env, { t: token, u: me.username || "", id: me.id || "" }));
  headers.append("Set-Cookie", cookie("kz_state", "", 0));
  return new Response(null, { status: 302, headers });
}
