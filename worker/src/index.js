const EVENTS = new Set([
  "visitor_arrived", "page_engaged", "level_selected", "path_selected",
  "search_performed", "search_no_result", "tutorial_opened", "tutorial_started",
  "tutorial_completed", "tutorial_abandoned", "next_tutorial_clicked",
  "topic_requested", "share_clicked", "return_visit"
]);

function reply(body, status, origin) {
  return new Response(body, {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff"
    }
  });
}

function text(value, max) {
  return String(value || "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, max);
}

function redact(value) {
  return value
    .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "[email]")
    .replace(/(?:\+?98|0)?9\d{9}/g, "[phone]")
    .replace(/(?:sk-|api[_-]?key\s*[:=])\S+/gi, "[secret]");
}

export default {
  async fetch(request, env) {
    const allowed = env.ALLOWED_ORIGIN || "https://mygravel.ir";
    const origin = request.headers.get("origin") || "";
    if (origin !== allowed) return reply('{"error":"origin_not_allowed"}', 403, allowed);
    if (request.method === "OPTIONS") return reply("{}", 204, allowed);
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/v1/events") return reply('{"error":"not_found"}', 404, allowed);
    if (!request.headers.get("content-type")?.toLowerCase().includes("application/json")) return reply('{"error":"json_required"}', 415, allowed);
    if (Number(request.headers.get("content-length") || 0) > 8192) return reply('{"error":"too_large"}', 413, allowed);

    let data;
    try { data = await request.json(); } catch (_) { return reply('{"error":"invalid_json"}', 400, allowed); }
    const event = text(data.event, 50);
    if (!EVENTS.has(event)) return reply('{"error":"invalid_event"}', 400, allowed);
    const props = data.properties && typeof data.properties === "object" ? data.properties : {};
    const propertyText = redact(JSON.stringify(props).slice(0, 1000));

    // IP و User-Agent عمداً نوشته نمی‌شوند. Analytics Engine داده را تجمیعی نگه می‌دارد.
    env.EVENTS.writeDataPoint({
      blobs: [event, text(data.visitorId, 64), text(data.sessionId, 64), text(data.path, 240), text(data.referrerHost, 120), propertyText],
      doubles: [Date.parse(data.occurredAt) || Date.now()],
      indexes: [text(data.visitorId, 64)]
    });
    return reply('{"ok":true}', 202, allowed);
  }
};
