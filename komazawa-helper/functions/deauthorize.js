// Meta 在用戶取消授權時呼叫。本網站不在伺服器保存任何用戶資料，只需回 200。
export async function onRequestPost() {
  return new Response("ok");
}
