// netlify/functions/ai-generate.js
const fetch = globalThis.fetch || (function(){ try { return require('node-fetch'); } catch(e){ return null } })();

exports.handler = async function(event, context) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers: { 'Content-Type': 'text/plain' }, body: 'Method Not Allowed' };
  }
  try {
    const apiKey = process.env.ZHIPU_API_KEY;
    if (!apiKey) {
      return { statusCode: 500, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ error: 'API Key 未配置' }) };
    }
    const payload = (() => {
      try { return JSON.parse(event.body || '{}'); } catch (e) { return {}; }
    })();

    const body = Object.assign({ model: 'glm-4-flash' }, payload);

    if (!fetch) {
      return { statusCode: 500, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ error: 'fetch 未就绪，请安装 node-fetch 或使用支持 fetch 的 Node 运行时' }) };
    }

    // 调试信息：打印接收到的 payload（不包含 apiKey）
    console.error('AI gateway payload:', Object.assign({}, body, { apiKey: undefined }));

    const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body)
    });

    const respText = await response.text();
    console.error('Upstream status:', response.status, 'body:', respText);

    // 尝试解析为 JSON，否则把原文返回以便调试
    let data;
    try { data = JSON.parse(respText); } catch (e) { data = { raw: respText }; }

    // 若上游返回非 200，返回详细信息以便定位问题（临时调试）
    if (!response.ok) {
      return {
        statusCode: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Upstream API error', status: response.status, body: data })
      };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    };
  } catch (error) {
    return { statusCode: 500, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ error: 'AI 调用失败', detail: String(error) }) };
  }
};