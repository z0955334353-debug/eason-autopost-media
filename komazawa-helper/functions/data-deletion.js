// Meta 在用戶要求刪除資料時呼叫。本網站不在伺服器保存任何用戶資料，回傳查詢頁與確認碼。
export async function onRequestPost({ request }) {
  const code = crypto.randomUUID().slice(0, 8);
  const url = new URL(`/data-deletion.html?code=${code}`, request.url).toString();
  return new Response(JSON.stringify({ url, confirmation_code: code }), { headers: { "Content-Type": "application/json" } });
}
