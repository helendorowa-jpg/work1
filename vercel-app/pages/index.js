import Head from "next/head";

export default function Home() {
  return (
    <>
      <Head>
        <title>海外内容运营 AI 面板</title>
        <meta httpEquiv="refresh" content="0; url=/index.html" />
      </Head>
      <main style={{ padding: 16, fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif" }}>
        <h1 style={{ margin: "0 0 8px" }}>海外内容运营 AI 面板</h1>
        <p style={{ margin: 0 }}>
          如果没有自动跳转，请点击 <a href="/index.html">打开工具</a>。
        </p>
      </main>
    </>
  );
}

