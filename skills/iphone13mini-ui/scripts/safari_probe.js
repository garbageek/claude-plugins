(() => {
  const probe = document.createElement("div");
  probe.style.cssText = "all:initial!important;position:fixed!important;visibility:hidden!important;" +
    "pointer-events:none!important;left:0!important;top:0!important;width:0!important;" +
    "height:0!important;padding:0!important;border:0!important;box-sizing:content-box!important;";
  document.documentElement.appendChild(probe);
  const measure = (property, value) => {
    probe.style.setProperty(property, value, "important");
    const result = getComputedStyle(probe).getPropertyValue(property);
    probe.style.setProperty(property, "0px", "important");
    return result;
  };
  try {
    const vv = window.visualViewport;
    return {
      url: location.href,
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      screen: {width: screen.width, height: screen.height},
      devicePixelRatio,
      window: {innerWidth, innerHeight, outerWidth, outerHeight, scrollX, scrollY},
      layoutViewport: {
        clientWidth: document.documentElement.clientWidth,
        clientHeight: document.documentElement.clientHeight,
      },
      visualViewport: vv ? {
        width: vv.width, height: vv.height, scale: vv.scale,
        offsetTop: vv.offsetTop, offsetLeft: vv.offsetLeft,
        pageTop: vv.pageTop, pageLeft: vv.pageLeft,
      } : null,
      document: {
        scrollWidth: document.documentElement.scrollWidth,
        scrollHeight: document.documentElement.scrollHeight,
      },
      viewportMeta: document.querySelector('meta[name="viewport"]')?.content ?? null,
      standalone: matchMedia("(display-mode: standalone)").matches || navigator.standalone === true,
      media: {
        coarse: matchMedia("(pointer: coarse)").matches,
        hover: matchMedia("(hover: hover)").matches,
        colorSchemeDark: matchMedia("(prefers-color-scheme: dark)").matches,
      },
      css: {
        vh: measure("height", "100vh"),
        svh: measure("height", "100svh"),
        lvh: measure("height", "100lvh"),
        dvh: measure("height", "100dvh"),
        safeAreaTop: measure("padding-top", "env(safe-area-inset-top, 0px)"),
        safeAreaRight: measure("padding-right", "env(safe-area-inset-right, 0px)"),
        safeAreaBottom: measure("padding-bottom", "env(safe-area-inset-bottom, 0px)"),
        safeAreaLeft: measure("padding-left", "env(safe-area-inset-left, 0px)"),
      },
      fonts: {status: document.fonts?.status ?? "unsupported"},
      readyState: document.readyState,
    };
  } finally {
    probe.remove();
  }
})();
