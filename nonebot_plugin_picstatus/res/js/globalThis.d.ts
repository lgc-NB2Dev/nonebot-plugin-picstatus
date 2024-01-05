declare module globalThis {
  var plugins: (() => Promise<any>)[];
}
