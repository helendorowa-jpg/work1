export default async function handler(req, res) {
  // CORS (harmless even when same-origin)
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }

  if (req.method !== "POST") {
    res.status(405).json({ error: { message: "Method Not Allowed" } });
    return;
  }

  const upstreamBaseUrl = (process.env.UPSTREAM_BASE_URL || "https://maas-api.cn-huabei-1.xf-yun.com/v2").replace(/\/$/, "");
  const upstreamApiKey = (process.env.UPSTREAM_API_KEY || "").trim();

  if (!upstreamApiKey) {
    res.status(500).json({
      error: {
        message:
          "Server not configured: missing UPSTREAM_API_KEY. Set it in Vercel Project Settings → Environment Variables."
      }
    });
    return;
  }

  const upstreamUrl = `${upstreamBaseUrl}/chat/completions`;

  try {
    const upstreamResp = await fetch(upstreamUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${upstreamApiKey}`
      },
      body: typeof req.body === "string" ? req.body : JSON.stringify(req.body)
    });

    const contentType = upstreamResp.headers.get("content-type") || "application/json; charset=utf-8";
    const text = await upstreamResp.text();
    res.status(upstreamResp.status);
    res.setHeader("Content-Type", contentType);
    res.send(text);
  } catch (e) {
    res.status(502).json({ error: { message: `Upstream fetch failed: ${e?.message || "unknown error"}` } });
  }
}

