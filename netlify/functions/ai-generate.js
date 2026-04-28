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

    const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    };
  } catch (error) {
    return { statusCode: 500, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ error: 'AI 调用失败', detail: String(error) }) };
  }
};