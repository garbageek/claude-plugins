/*
 * Run on the actual iPhone Safari page via Safari Web Inspector or an iOS Shortcut
 * (Run JavaScript on Web Page). No remote network calls. It shows measured viewport
 * values and a Copy JSON button. Run separately from reference screenshot capture.
 */
(() => {
  const measure = (property, value) => {
    const element = document.createElement("div");
    element.style.cssText = "position:absolute;left:-99999px;top:0;visibility:hidden;";
    element.style.setProperty(property, value);
    document.documentElement.appendChild(element);
    const result = getComputedStyle(element).getPropertyValue(property);
    element.remove();
    return result;
  };
  const rect = (selector) => {
    const node = document.querySelector(selector);
    if (!node) return null;
    const box = node.getBoundingClientRect();
    return {x: box.x, y: box.y, width: box.width, height: box.height};
  };
  const viewport = window.visualViewport;
  const data = {
    url: location.href,
    capturedAt: new Date().toISOString(),
    ua: navigator.userAgent,
    screen: {width: screen.width, height: screen.height},
    dpr: devicePixelRatio,
    inner: {width: innerWidth, height: innerHeight, scrollX, scrollY},
    visualViewport: viewport ? {
      width: viewport.width, height: viewport.height,
      offsetTop: viewport.offsetTop, offsetLeft: viewport.offsetLeft,
      pageTop: viewport.pageTop, pageLeft: viewport.pageLeft,
      scale: viewport.scale,
    } : null,
    viewportMeta: document.querySelector('meta[name="viewport"]')?.content ?? null,
    css: {
      vh: measure("height", "100vh"),
      svh: measure("height", "100svh"),
      lvh: measure("height", "100lvh"),
      dvh: measure("height", "100dvh"),
      safeTop: measure("padding-top", "env(safe-area-inset-top)"),
      safeBottom: measure("padding-bottom", "env(safe-area-inset-bottom)"),
      safeLeft: measure("padding-left", "env(safe-area-inset-left)"),
      safeRight: measure("padding-right", "env(safe-area-inset-right)"),
    },
    anchors: {
      h1: rect("h1"),
      header: rect("header"),
      main: rect("main"),
      footer: rect("footer"),
    },
  };
  const json = JSON.stringify(data, null, 2);
  window.__iphone13miniCalibration = data;
  console.log(json);
  document.getElementById("__iphone13mini_probe")?.remove();
  const panel = document.createElement("div");
  panel.id = "__iphone13mini_probe";
  panel.style.cssText = "position:fixed;z-index:2147483647;inset:12% 4% 8%;padding:16px;" +
    "background:#111;color:#fff;box-sizing:border-box;border:2px solid #fff;" +
    "font:12px/1.5 monospace;overflow:auto;user-select:text;";
  const pre = document.createElement("pre");
  pre.style.cssText = "white-space:pre-wrap;overflow-wrap:anywhere;";
  pre.textContent = json;
  const copy = document.createElement("button");
  copy.textContent = "Copy JSON";
  copy.style.cssText = "font:16px sans-serif;padding:10px;";
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(json); copy.textContent = "Copied"; }
    catch { copy.textContent = "Select the JSON below to copy"; }
  });
  const close = document.createElement("button");
  close.textContent = "Close";
  close.style.cssText = "font:16px sans-serif;padding:10px;margin-left:10px;";
  close.addEventListener("click", () => panel.remove());
  panel.append(copy, close, pre);
  document.body.appendChild(panel);
  if (typeof completion === "function") completion(json);
  return data;
})();
