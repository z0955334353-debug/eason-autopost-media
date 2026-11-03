// 共用：Threads API、加密 session cookie
export const APP_ID = "1124882513618266"; // Threads 應用程式編號（公開資訊）
export const SCOPES = [
  "threads_basic",
  "threads_content_publish",
  "threads_read_replies",
  "threads_manage_replies",
  "threads_keyword_search",
].join(",");
const COOKIE = "kz_session";

export function redirectUri(request) {
  return new URL("/callback", request.url).toString();
}

async function key(env) {
  const raw = new TextEncoder().encode("kz-session:" + (env.THREADS_APP_SECRET || ""));
  const hash = await crypto.subtle.digest("SHA-256", raw);
  return crypto.subtle.importKey("raw", hash, "AES-GCM", false, ["encrypt", "decrypt"]);
}
const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64 = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));

export async function seal(env, obj) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await key(env), new TextEncoder().encode(JSON.stringify(obj)));
  return b64(iv) + "." + b64(ct);
}
export async function unseal(env, s) {
  try {
    const [iv, ct] = s.split(".");
    const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(iv) }, await key(env), unb64(ct));
    return JSON.parse(new TextDecoder().decode(pt));
  } catch {
    return null;
  }
}
export function cookie(name, value, maxAge) {
  return `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}
export function readCookie(request, name) {
  const m = (request.headers.get("Cookie") || "").match(new RegExp(`(?:^|; )${name}=([^;]+)`));
  return m ? m[1] : null;
}
export async function session(request, env) {
  const c = readCookie(request, COOKIE);
  if (!c) return null;
  const s = await unseal(env, c);
  if (!s || !s.t || (s.exp && Date.now() > s.exp)) return null;
  return s;
}
export async function setSession(env, data) {
  const maxAge = 50 * 24 * 3600;
  return cookie(COOKIE, await seal(env, { ...data, exp: Date.now() + maxAge * 1000 }), maxAge);
}
export const clearSession = () => cookie(COOKIE, "", 0);

export function json(obj, status = 200, headers = {}) {
  return new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json; charset=utf-8", ...headers } });
}

export async function threads(method, path, params, token) {
  const url = new URL(`https://graph.threads.net/v1.0/${path}`);
  const body = new URLSearchParams({ ...params, access_token: token });
  let res;
  if (method === "GET") {
    for (const [k, v] of body) url.searchParams.set(k, v);
    res = await fetch(url);
  } else {
    res = await fetch(url, { method: "POST", body });
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    const msg = (data.error && data.error.message) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}
