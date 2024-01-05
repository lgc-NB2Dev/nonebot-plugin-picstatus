/// <reference path="./globalThis.d.ts" />
(() => {
  /**
   * @template {any[]} A
   * @template R
   * @param {(...args: A) => Promise<R>} func
   * @returns {(...args: A) => Promise<R | undefined>}
   */
  function wrapErr(func) {
    return async (...args) => {
      try {
        return await func(...args);
      } catch (e) {
        console.error(e);
      }
    };
  }

  /**
   * @param {string} url
   */
  async function makeObjUrlFromUrl(url) {
    const res = await fetch(url);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  }

  /** @typedef {(elem: HTMLElement, objUrl: string) => Promise<any>} PropSetterType */

  /** @type {Record<string, PropSetterType>} */
  const propSetterMap = {
    'data-background-image': async (elem, objUrl) => {
      elem.style.backgroundImage = `url(${objUrl})`;
    },
    'data-src': async (elem, objUrl) => {
      if (elem instanceof HTMLImageElement) elem.src = objUrl;
    },
  };

  /**
   * @param {HTMLElement} elem
   * @param {string} attr
   * @param {PropSetterType} setter
   */
  async function lazyLoadOne(elem, attr, setter) {
    const url = elem.getAttribute(attr);
    if (!url) return;
    const objUrl = await makeObjUrlFromUrl(url);
    await setter(elem, objUrl);
    elem.removeAttribute(attr);
  }

  /**
   * @param {string} attr
   */
  async function lazyLoad(attr) {
    /** @type {HTMLElement[]} */
    // @ts-ignore
    const elements = [...document.body.querySelectorAll(`[${attr}]`)].filter(
      (v) => v instanceof HTMLElement
    );
    const tasks = elements.map((v) =>
      wrapErr(lazyLoadOne)(v, attr, propSetterMap[attr])
    );
    await Promise.all(tasks);
  }

  async function lazyLoadAll() {
    await Promise.all(Object.keys(propSetterMap).map(lazyLoad));
  }

  // 使用 globalThis.plugins.push 注册插件
  // 只有这样才能保证你的插件运行完成之后才会网页截图
  globalThis.plugins.push(async () => {
    await lazyLoadAll();
  });
})();
