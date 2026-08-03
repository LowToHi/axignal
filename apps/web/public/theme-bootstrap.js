(function bootstrapAxignalTheme() {
  try {
    var theme = window.localStorage.getItem("axignal:subscriber:theme");
    if (theme !== "light" && theme !== "dark") return;
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
  } catch {
    // Storage can be unavailable in a hardened browser context. The server cookie remains authoritative.
  }
})();
