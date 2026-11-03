import { session, json } from "../../lib/threads.js";
export async function onRequestGet({ request, env }) {
  const s = await session(request, env);
  return json(s ? { loggedIn: true, username: s.u } : { loggedIn: false });
}
