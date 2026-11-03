import { APP_ID, SCOPES, redirectUri, cookie } from "../lib/threads.js";

export async function onRequestGet({ request }) {
  const state = crypto.randomUUID();
  const u = new URL("https://threads.net/oauth/authorize");
  u.searchParams.set("client_id", APP_ID);
  u.searchParams.set("redirect_uri", redirectUri(request));
  u.searchParams.set("scope", SCOPES);
  u.searchParams.set("response_type", "code");
  u.searchParams.set("state", state);
  return new Response(null, { status: 302, headers: { Location: u.toString(), "Set-Cookie": cookie("kz_state", state, 600) } });
}
