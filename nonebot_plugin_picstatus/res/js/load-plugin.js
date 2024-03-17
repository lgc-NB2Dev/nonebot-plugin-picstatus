(async () => {
  for (const plugin of globalThis.plugins) {
    try {
      await plugin();
    } catch (e) {
      console.error(e);
    }
  }
  document.body.classList.add('done');
})();
