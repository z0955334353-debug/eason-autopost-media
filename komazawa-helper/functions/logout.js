import { clearSession } from "../lib/threads.js";
export async function onRequestGet() {
  return new Response(null, { status: 302, headers: { Location: "/", "Set-Cookie": clearSession() } });
}
