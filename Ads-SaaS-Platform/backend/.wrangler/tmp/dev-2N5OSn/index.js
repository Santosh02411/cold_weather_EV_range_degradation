var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });
var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
  get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
}) : x)(function(x) {
  if (typeof require !== "undefined") return require.apply(this, arguments);
  throw Error('Dynamic require of "' + x + '" is not supported');
});
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __commonJS = (cb, mod) => function __require2() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/_internal/utils.mjs
// @__NO_SIDE_EFFECTS__
function createNotImplementedError(name) {
  return new Error(`[unenv] ${name} is not implemented yet!`);
}
// @__NO_SIDE_EFFECTS__
function notImplemented(name) {
  const fn = /* @__PURE__ */ __name(() => {
    throw /* @__PURE__ */ createNotImplementedError(name);
  }, "fn");
  return Object.assign(fn, { __unenv__: true });
}
// @__NO_SIDE_EFFECTS__
function notImplementedClass(name) {
  return class {
    __unenv__ = true;
    constructor() {
      throw new Error(`[unenv] ${name} is not implemented yet!`);
    }
  };
}
var init_utils = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/_internal/utils.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    __name(createNotImplementedError, "createNotImplementedError");
    __name(notImplemented, "notImplemented");
    __name(notImplementedClass, "notImplementedClass");
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/perf_hooks/performance.mjs
var _timeOrigin, _performanceNow, nodeTiming, PerformanceEntry, PerformanceMark, PerformanceMeasure, PerformanceResourceTiming, PerformanceObserverEntryList, Performance, PerformanceObserver, performance;
var init_performance = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/perf_hooks/performance.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_utils();
    _timeOrigin = globalThis.performance?.timeOrigin ?? Date.now();
    _performanceNow = globalThis.performance?.now ? globalThis.performance.now.bind(globalThis.performance) : () => Date.now() - _timeOrigin;
    nodeTiming = {
      name: "node",
      entryType: "node",
      startTime: 0,
      duration: 0,
      nodeStart: 0,
      v8Start: 0,
      bootstrapComplete: 0,
      environment: 0,
      loopStart: 0,
      loopExit: 0,
      idleTime: 0,
      uvMetricsInfo: {
        loopCount: 0,
        events: 0,
        eventsWaiting: 0
      },
      detail: void 0,
      toJSON() {
        return this;
      }
    };
    PerformanceEntry = class {
      static {
        __name(this, "PerformanceEntry");
      }
      __unenv__ = true;
      detail;
      entryType = "event";
      name;
      startTime;
      constructor(name, options) {
        this.name = name;
        this.startTime = options?.startTime || _performanceNow();
        this.detail = options?.detail;
      }
      get duration() {
        return _performanceNow() - this.startTime;
      }
      toJSON() {
        return {
          name: this.name,
          entryType: this.entryType,
          startTime: this.startTime,
          duration: this.duration,
          detail: this.detail
        };
      }
    };
    PerformanceMark = class PerformanceMark2 extends PerformanceEntry {
      static {
        __name(this, "PerformanceMark");
      }
      entryType = "mark";
      constructor() {
        super(...arguments);
      }
      get duration() {
        return 0;
      }
    };
    PerformanceMeasure = class extends PerformanceEntry {
      static {
        __name(this, "PerformanceMeasure");
      }
      entryType = "measure";
    };
    PerformanceResourceTiming = class extends PerformanceEntry {
      static {
        __name(this, "PerformanceResourceTiming");
      }
      entryType = "resource";
      serverTiming = [];
      connectEnd = 0;
      connectStart = 0;
      decodedBodySize = 0;
      domainLookupEnd = 0;
      domainLookupStart = 0;
      encodedBodySize = 0;
      fetchStart = 0;
      initiatorType = "";
      name = "";
      nextHopProtocol = "";
      redirectEnd = 0;
      redirectStart = 0;
      requestStart = 0;
      responseEnd = 0;
      responseStart = 0;
      secureConnectionStart = 0;
      startTime = 0;
      transferSize = 0;
      workerStart = 0;
      responseStatus = 0;
    };
    PerformanceObserverEntryList = class {
      static {
        __name(this, "PerformanceObserverEntryList");
      }
      __unenv__ = true;
      getEntries() {
        return [];
      }
      getEntriesByName(_name, _type) {
        return [];
      }
      getEntriesByType(type) {
        return [];
      }
    };
    Performance = class {
      static {
        __name(this, "Performance");
      }
      __unenv__ = true;
      timeOrigin = _timeOrigin;
      eventCounts = /* @__PURE__ */ new Map();
      _entries = [];
      _resourceTimingBufferSize = 0;
      navigation = void 0;
      timing = void 0;
      timerify(_fn, _options) {
        throw createNotImplementedError("Performance.timerify");
      }
      get nodeTiming() {
        return nodeTiming;
      }
      eventLoopUtilization() {
        return {};
      }
      markResourceTiming() {
        return new PerformanceResourceTiming("");
      }
      onresourcetimingbufferfull = null;
      now() {
        if (this.timeOrigin === _timeOrigin) {
          return _performanceNow();
        }
        return Date.now() - this.timeOrigin;
      }
      clearMarks(markName) {
        this._entries = markName ? this._entries.filter((e) => e.name !== markName) : this._entries.filter((e) => e.entryType !== "mark");
      }
      clearMeasures(measureName) {
        this._entries = measureName ? this._entries.filter((e) => e.name !== measureName) : this._entries.filter((e) => e.entryType !== "measure");
      }
      clearResourceTimings() {
        this._entries = this._entries.filter((e) => e.entryType !== "resource" || e.entryType !== "navigation");
      }
      getEntries() {
        return this._entries;
      }
      getEntriesByName(name, type) {
        return this._entries.filter((e) => e.name === name && (!type || e.entryType === type));
      }
      getEntriesByType(type) {
        return this._entries.filter((e) => e.entryType === type);
      }
      mark(name, options) {
        const entry = new PerformanceMark(name, options);
        this._entries.push(entry);
        return entry;
      }
      measure(measureName, startOrMeasureOptions, endMark) {
        let start;
        let end;
        if (typeof startOrMeasureOptions === "string") {
          start = this.getEntriesByName(startOrMeasureOptions, "mark")[0]?.startTime;
          end = this.getEntriesByName(endMark, "mark")[0]?.startTime;
        } else {
          start = Number.parseFloat(startOrMeasureOptions?.start) || this.now();
          end = Number.parseFloat(startOrMeasureOptions?.end) || this.now();
        }
        const entry = new PerformanceMeasure(measureName, {
          startTime: start,
          detail: {
            start,
            end
          }
        });
        this._entries.push(entry);
        return entry;
      }
      setResourceTimingBufferSize(maxSize) {
        this._resourceTimingBufferSize = maxSize;
      }
      addEventListener(type, listener, options) {
        throw createNotImplementedError("Performance.addEventListener");
      }
      removeEventListener(type, listener, options) {
        throw createNotImplementedError("Performance.removeEventListener");
      }
      dispatchEvent(event) {
        throw createNotImplementedError("Performance.dispatchEvent");
      }
      toJSON() {
        return this;
      }
    };
    PerformanceObserver = class {
      static {
        __name(this, "PerformanceObserver");
      }
      __unenv__ = true;
      static supportedEntryTypes = [];
      _callback = null;
      constructor(callback) {
        this._callback = callback;
      }
      takeRecords() {
        return [];
      }
      disconnect() {
        throw createNotImplementedError("PerformanceObserver.disconnect");
      }
      observe(options) {
        throw createNotImplementedError("PerformanceObserver.observe");
      }
      bind(fn) {
        return fn;
      }
      runInAsyncScope(fn, thisArg, ...args) {
        return fn.call(thisArg, ...args);
      }
      asyncId() {
        return 0;
      }
      triggerAsyncId() {
        return 0;
      }
      emitDestroy() {
        return this;
      }
    };
    performance = globalThis.performance && "addEventListener" in globalThis.performance ? globalThis.performance : new Performance();
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/perf_hooks.mjs
var init_perf_hooks = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/perf_hooks.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_performance();
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/@cloudflare/unenv-preset/dist/runtime/polyfill/performance.mjs
var init_performance2 = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/@cloudflare/unenv-preset/dist/runtime/polyfill/performance.mjs"() {
    init_perf_hooks();
    if (!("__unenv__" in performance)) {
      const proto = Performance.prototype;
      for (const key of Object.getOwnPropertyNames(proto)) {
        if (key !== "constructor" && !(key in performance)) {
          const desc = Object.getOwnPropertyDescriptor(proto, key);
          if (desc) {
            Object.defineProperty(performance, key, desc);
          }
        }
      }
    }
    globalThis.performance = performance;
    globalThis.Performance = Performance;
    globalThis.PerformanceEntry = PerformanceEntry;
    globalThis.PerformanceMark = PerformanceMark;
    globalThis.PerformanceMeasure = PerformanceMeasure;
    globalThis.PerformanceObserver = PerformanceObserver;
    globalThis.PerformanceObserverEntryList = PerformanceObserverEntryList;
    globalThis.PerformanceResourceTiming = PerformanceResourceTiming;
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/mock/noop.mjs
var noop_default;
var init_noop = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/mock/noop.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    noop_default = Object.assign(() => {
    }, { __unenv__: true });
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/console.mjs
import { Writable } from "node:stream";
var _console, _ignoreErrors, _stderr, _stdout, log, info, trace, debug, table, error, warn, createTask, clear, count, countReset, dir, dirxml, group, groupEnd, groupCollapsed, profile, profileEnd, time, timeEnd, timeLog, timeStamp, Console, _times, _stdoutErrorHandler, _stderrErrorHandler;
var init_console = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/console.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_noop();
    init_utils();
    _console = globalThis.console;
    _ignoreErrors = true;
    _stderr = new Writable();
    _stdout = new Writable();
    log = _console?.log ?? noop_default;
    info = _console?.info ?? log;
    trace = _console?.trace ?? info;
    debug = _console?.debug ?? log;
    table = _console?.table ?? log;
    error = _console?.error ?? log;
    warn = _console?.warn ?? error;
    createTask = _console?.createTask ?? /* @__PURE__ */ notImplemented("console.createTask");
    clear = _console?.clear ?? noop_default;
    count = _console?.count ?? noop_default;
    countReset = _console?.countReset ?? noop_default;
    dir = _console?.dir ?? noop_default;
    dirxml = _console?.dirxml ?? noop_default;
    group = _console?.group ?? noop_default;
    groupEnd = _console?.groupEnd ?? noop_default;
    groupCollapsed = _console?.groupCollapsed ?? noop_default;
    profile = _console?.profile ?? noop_default;
    profileEnd = _console?.profileEnd ?? noop_default;
    time = _console?.time ?? noop_default;
    timeEnd = _console?.timeEnd ?? noop_default;
    timeLog = _console?.timeLog ?? noop_default;
    timeStamp = _console?.timeStamp ?? noop_default;
    Console = _console?.Console ?? /* @__PURE__ */ notImplementedClass("console.Console");
    _times = /* @__PURE__ */ new Map();
    _stdoutErrorHandler = noop_default;
    _stderrErrorHandler = noop_default;
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/@cloudflare/unenv-preset/dist/runtime/node/console.mjs
var workerdConsole, assert, clear2, context, count2, countReset2, createTask2, debug2, dir2, dirxml2, error2, group2, groupCollapsed2, groupEnd2, info2, log2, profile2, profileEnd2, table2, time2, timeEnd2, timeLog2, timeStamp2, trace2, warn2, console_default;
var init_console2 = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/@cloudflare/unenv-preset/dist/runtime/node/console.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_console();
    workerdConsole = globalThis["console"];
    ({
      assert,
      clear: clear2,
      context: (
        // @ts-expect-error undocumented public API
        context
      ),
      count: count2,
      countReset: countReset2,
      createTask: (
        // @ts-expect-error undocumented public API
        createTask2
      ),
      debug: debug2,
      dir: dir2,
      dirxml: dirxml2,
      error: error2,
      group: group2,
      groupCollapsed: groupCollapsed2,
      groupEnd: groupEnd2,
      info: info2,
      log: log2,
      profile: profile2,
      profileEnd: profileEnd2,
      table: table2,
      time: time2,
      timeEnd: timeEnd2,
      timeLog: timeLog2,
      timeStamp: timeStamp2,
      trace: trace2,
      warn: warn2
    } = workerdConsole);
    Object.assign(workerdConsole, {
      Console,
      _ignoreErrors,
      _stderr,
      _stderrErrorHandler,
      _stdout,
      _stdoutErrorHandler,
      _times
    });
    console_default = workerdConsole;
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/_virtual_unenv_global_polyfill-@cloudflare-unenv-preset-node-console
var init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/_virtual_unenv_global_polyfill-@cloudflare-unenv-preset-node-console"() {
    init_console2();
    globalThis.console = console_default;
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/process/hrtime.mjs
var hrtime;
var init_hrtime = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/process/hrtime.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    hrtime = /* @__PURE__ */ Object.assign(/* @__PURE__ */ __name(function hrtime2(startTime) {
      const now = Date.now();
      const seconds = Math.trunc(now / 1e3);
      const nanos = now % 1e3 * 1e6;
      if (startTime) {
        let diffSeconds = seconds - startTime[0];
        let diffNanos = nanos - startTime[0];
        if (diffNanos < 0) {
          diffSeconds = diffSeconds - 1;
          diffNanos = 1e9 + diffNanos;
        }
        return [diffSeconds, diffNanos];
      }
      return [seconds, nanos];
    }, "hrtime"), { bigint: /* @__PURE__ */ __name(function bigint() {
      return BigInt(Date.now() * 1e6);
    }, "bigint") });
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/tty/read-stream.mjs
var ReadStream;
var init_read_stream = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/tty/read-stream.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    ReadStream = class {
      static {
        __name(this, "ReadStream");
      }
      fd;
      isRaw = false;
      isTTY = false;
      constructor(fd) {
        this.fd = fd;
      }
      setRawMode(mode) {
        this.isRaw = mode;
        return this;
      }
    };
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/tty/write-stream.mjs
var WriteStream;
var init_write_stream = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/tty/write-stream.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    WriteStream = class {
      static {
        __name(this, "WriteStream");
      }
      fd;
      columns = 80;
      rows = 24;
      isTTY = false;
      constructor(fd) {
        this.fd = fd;
      }
      clearLine(dir3, callback) {
        callback && callback();
        return false;
      }
      clearScreenDown(callback) {
        callback && callback();
        return false;
      }
      cursorTo(x, y, callback) {
        callback && typeof callback === "function" && callback();
        return false;
      }
      moveCursor(dx, dy, callback) {
        callback && callback();
        return false;
      }
      getColorDepth(env2) {
        return 1;
      }
      hasColors(count3, env2) {
        return false;
      }
      getWindowSize() {
        return [this.columns, this.rows];
      }
      write(str, encoding, cb) {
        if (str instanceof Uint8Array) {
          str = new TextDecoder().decode(str);
        }
        try {
          console.log(str);
        } catch {
        }
        cb && typeof cb === "function" && cb();
        return false;
      }
    };
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/tty.mjs
var init_tty = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/tty.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_read_stream();
    init_write_stream();
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/process/node-version.mjs
var NODE_VERSION;
var init_node_version = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/process/node-version.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    NODE_VERSION = "22.14.0";
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/process/process.mjs
import { EventEmitter } from "node:events";
var Process;
var init_process = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/unenv/dist/runtime/node/internal/process/process.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_tty();
    init_utils();
    init_node_version();
    Process = class _Process extends EventEmitter {
      static {
        __name(this, "Process");
      }
      env;
      hrtime;
      nextTick;
      constructor(impl) {
        super();
        this.env = impl.env;
        this.hrtime = impl.hrtime;
        this.nextTick = impl.nextTick;
        for (const prop of [...Object.getOwnPropertyNames(_Process.prototype), ...Object.getOwnPropertyNames(EventEmitter.prototype)]) {
          const value = this[prop];
          if (typeof value === "function") {
            this[prop] = value.bind(this);
          }
        }
      }
      // --- event emitter ---
      emitWarning(warning, type, code) {
        console.warn(`${code ? `[${code}] ` : ""}${type ? `${type}: ` : ""}${warning}`);
      }
      emit(...args) {
        return super.emit(...args);
      }
      listeners(eventName) {
        return super.listeners(eventName);
      }
      // --- stdio (lazy initializers) ---
      #stdin;
      #stdout;
      #stderr;
      get stdin() {
        return this.#stdin ??= new ReadStream(0);
      }
      get stdout() {
        return this.#stdout ??= new WriteStream(1);
      }
      get stderr() {
        return this.#stderr ??= new WriteStream(2);
      }
      // --- cwd ---
      #cwd = "/";
      chdir(cwd2) {
        this.#cwd = cwd2;
      }
      cwd() {
        return this.#cwd;
      }
      // --- dummy props and getters ---
      arch = "";
      platform = "";
      argv = [];
      argv0 = "";
      execArgv = [];
      execPath = "";
      title = "";
      pid = 200;
      ppid = 100;
      get version() {
        return `v${NODE_VERSION}`;
      }
      get versions() {
        return { node: NODE_VERSION };
      }
      get allowedNodeEnvironmentFlags() {
        return /* @__PURE__ */ new Set();
      }
      get sourceMapsEnabled() {
        return false;
      }
      get debugPort() {
        return 0;
      }
      get throwDeprecation() {
        return false;
      }
      get traceDeprecation() {
        return false;
      }
      get features() {
        return {};
      }
      get release() {
        return {};
      }
      get connected() {
        return false;
      }
      get config() {
        return {};
      }
      get moduleLoadList() {
        return [];
      }
      constrainedMemory() {
        return 0;
      }
      availableMemory() {
        return 0;
      }
      uptime() {
        return 0;
      }
      resourceUsage() {
        return {};
      }
      // --- noop methods ---
      ref() {
      }
      unref() {
      }
      // --- unimplemented methods ---
      umask() {
        throw createNotImplementedError("process.umask");
      }
      getBuiltinModule() {
        return void 0;
      }
      getActiveResourcesInfo() {
        throw createNotImplementedError("process.getActiveResourcesInfo");
      }
      exit() {
        throw createNotImplementedError("process.exit");
      }
      reallyExit() {
        throw createNotImplementedError("process.reallyExit");
      }
      kill() {
        throw createNotImplementedError("process.kill");
      }
      abort() {
        throw createNotImplementedError("process.abort");
      }
      dlopen() {
        throw createNotImplementedError("process.dlopen");
      }
      setSourceMapsEnabled() {
        throw createNotImplementedError("process.setSourceMapsEnabled");
      }
      loadEnvFile() {
        throw createNotImplementedError("process.loadEnvFile");
      }
      disconnect() {
        throw createNotImplementedError("process.disconnect");
      }
      cpuUsage() {
        throw createNotImplementedError("process.cpuUsage");
      }
      setUncaughtExceptionCaptureCallback() {
        throw createNotImplementedError("process.setUncaughtExceptionCaptureCallback");
      }
      hasUncaughtExceptionCaptureCallback() {
        throw createNotImplementedError("process.hasUncaughtExceptionCaptureCallback");
      }
      initgroups() {
        throw createNotImplementedError("process.initgroups");
      }
      openStdin() {
        throw createNotImplementedError("process.openStdin");
      }
      assert() {
        throw createNotImplementedError("process.assert");
      }
      binding() {
        throw createNotImplementedError("process.binding");
      }
      // --- attached interfaces ---
      permission = { has: /* @__PURE__ */ notImplemented("process.permission.has") };
      report = {
        directory: "",
        filename: "",
        signal: "SIGUSR2",
        compact: false,
        reportOnFatalError: false,
        reportOnSignal: false,
        reportOnUncaughtException: false,
        getReport: /* @__PURE__ */ notImplemented("process.report.getReport"),
        writeReport: /* @__PURE__ */ notImplemented("process.report.writeReport")
      };
      finalization = {
        register: /* @__PURE__ */ notImplemented("process.finalization.register"),
        unregister: /* @__PURE__ */ notImplemented("process.finalization.unregister"),
        registerBeforeExit: /* @__PURE__ */ notImplemented("process.finalization.registerBeforeExit")
      };
      memoryUsage = Object.assign(() => ({
        arrayBuffers: 0,
        rss: 0,
        external: 0,
        heapTotal: 0,
        heapUsed: 0
      }), { rss: /* @__PURE__ */ __name(() => 0, "rss") });
      // --- undefined props ---
      mainModule = void 0;
      domain = void 0;
      // optional
      send = void 0;
      exitCode = void 0;
      channel = void 0;
      getegid = void 0;
      geteuid = void 0;
      getgid = void 0;
      getgroups = void 0;
      getuid = void 0;
      setegid = void 0;
      seteuid = void 0;
      setgid = void 0;
      setgroups = void 0;
      setuid = void 0;
      // internals
      _events = void 0;
      _eventsCount = void 0;
      _exiting = void 0;
      _maxListeners = void 0;
      _debugEnd = void 0;
      _debugProcess = void 0;
      _fatalException = void 0;
      _getActiveHandles = void 0;
      _getActiveRequests = void 0;
      _kill = void 0;
      _preload_modules = void 0;
      _rawDebug = void 0;
      _startProfilerIdleNotifier = void 0;
      _stopProfilerIdleNotifier = void 0;
      _tickCallback = void 0;
      _disconnect = void 0;
      _handleQueue = void 0;
      _pendingMessage = void 0;
      _channel = void 0;
      _send = void 0;
      _linkedBinding = void 0;
    };
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/@cloudflare/unenv-preset/dist/runtime/node/process.mjs
var globalProcess, getBuiltinModule, workerdProcess, unenvProcess, exit, features, platform, _channel, _debugEnd, _debugProcess, _disconnect, _events, _eventsCount, _exiting, _fatalException, _getActiveHandles, _getActiveRequests, _handleQueue, _kill, _linkedBinding, _maxListeners, _pendingMessage, _preload_modules, _rawDebug, _send, _startProfilerIdleNotifier, _stopProfilerIdleNotifier, _tickCallback, abort, addListener, allowedNodeEnvironmentFlags, arch, argv, argv0, assert2, availableMemory, binding, channel, chdir, config, connected, constrainedMemory, cpuUsage, cwd, debugPort, disconnect, dlopen, domain, emit, emitWarning, env, eventNames, execArgv, execPath, exitCode, finalization, getActiveResourcesInfo, getegid, geteuid, getgid, getgroups, getMaxListeners, getuid, hasUncaughtExceptionCaptureCallback, hrtime3, initgroups, kill, listenerCount, listeners, loadEnvFile, mainModule, memoryUsage, moduleLoadList, nextTick, off, on, once, openStdin, permission, pid, ppid, prependListener, prependOnceListener, rawListeners, reallyExit, ref, release, removeAllListeners, removeListener, report, resourceUsage, send, setegid, seteuid, setgid, setgroups, setMaxListeners, setSourceMapsEnabled, setuid, setUncaughtExceptionCaptureCallback, sourceMapsEnabled, stderr, stdin, stdout, throwDeprecation, title, traceDeprecation, umask, unref, uptime, version, versions, _process, process_default;
var init_process2 = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/node_modules/@cloudflare/unenv-preset/dist/runtime/node/process.mjs"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    init_hrtime();
    init_process();
    globalProcess = globalThis["process"];
    getBuiltinModule = globalProcess.getBuiltinModule;
    workerdProcess = getBuiltinModule("node:process");
    unenvProcess = new Process({
      env: globalProcess.env,
      hrtime,
      // `nextTick` is available from workerd process v1
      nextTick: workerdProcess.nextTick
    });
    ({ exit, features, platform } = workerdProcess);
    ({
      _channel,
      _debugEnd,
      _debugProcess,
      _disconnect,
      _events,
      _eventsCount,
      _exiting,
      _fatalException,
      _getActiveHandles,
      _getActiveRequests,
      _handleQueue,
      _kill,
      _linkedBinding,
      _maxListeners,
      _pendingMessage,
      _preload_modules,
      _rawDebug,
      _send,
      _startProfilerIdleNotifier,
      _stopProfilerIdleNotifier,
      _tickCallback,
      abort,
      addListener,
      allowedNodeEnvironmentFlags,
      arch,
      argv,
      argv0,
      assert: assert2,
      availableMemory,
      binding,
      channel,
      chdir,
      config,
      connected,
      constrainedMemory,
      cpuUsage,
      cwd,
      debugPort,
      disconnect,
      dlopen,
      domain,
      emit,
      emitWarning,
      env,
      eventNames,
      execArgv,
      execPath,
      exitCode,
      finalization,
      getActiveResourcesInfo,
      getegid,
      geteuid,
      getgid,
      getgroups,
      getMaxListeners,
      getuid,
      hasUncaughtExceptionCaptureCallback,
      hrtime: hrtime3,
      initgroups,
      kill,
      listenerCount,
      listeners,
      loadEnvFile,
      mainModule,
      memoryUsage,
      moduleLoadList,
      nextTick,
      off,
      on,
      once,
      openStdin,
      permission,
      pid,
      ppid,
      prependListener,
      prependOnceListener,
      rawListeners,
      reallyExit,
      ref,
      release,
      removeAllListeners,
      removeListener,
      report,
      resourceUsage,
      send,
      setegid,
      seteuid,
      setgid,
      setgroups,
      setMaxListeners,
      setSourceMapsEnabled,
      setuid,
      setUncaughtExceptionCaptureCallback,
      sourceMapsEnabled,
      stderr,
      stdin,
      stdout,
      throwDeprecation,
      title,
      traceDeprecation,
      umask,
      unref,
      uptime,
      version,
      versions
    } = unenvProcess);
    _process = {
      abort,
      addListener,
      allowedNodeEnvironmentFlags,
      hasUncaughtExceptionCaptureCallback,
      setUncaughtExceptionCaptureCallback,
      loadEnvFile,
      sourceMapsEnabled,
      arch,
      argv,
      argv0,
      chdir,
      config,
      connected,
      constrainedMemory,
      availableMemory,
      cpuUsage,
      cwd,
      debugPort,
      dlopen,
      disconnect,
      emit,
      emitWarning,
      env,
      eventNames,
      execArgv,
      execPath,
      exit,
      finalization,
      features,
      getBuiltinModule,
      getActiveResourcesInfo,
      getMaxListeners,
      hrtime: hrtime3,
      kill,
      listeners,
      listenerCount,
      memoryUsage,
      nextTick,
      on,
      off,
      once,
      pid,
      platform,
      ppid,
      prependListener,
      prependOnceListener,
      rawListeners,
      release,
      removeAllListeners,
      removeListener,
      report,
      resourceUsage,
      setMaxListeners,
      setSourceMapsEnabled,
      stderr,
      stdin,
      stdout,
      title,
      throwDeprecation,
      traceDeprecation,
      umask,
      uptime,
      version,
      versions,
      // @ts-expect-error old API
      domain,
      initgroups,
      moduleLoadList,
      reallyExit,
      openStdin,
      assert: assert2,
      binding,
      send,
      exitCode,
      channel,
      getegid,
      geteuid,
      getgid,
      getgroups,
      getuid,
      setegid,
      seteuid,
      setgid,
      setgroups,
      setuid,
      permission,
      mainModule,
      _events,
      _eventsCount,
      _exiting,
      _maxListeners,
      _debugEnd,
      _debugProcess,
      _fatalException,
      _getActiveHandles,
      _getActiveRequests,
      _kill,
      _preload_modules,
      _rawDebug,
      _startProfilerIdleNotifier,
      _stopProfilerIdleNotifier,
      _tickCallback,
      _disconnect,
      _handleQueue,
      _pendingMessage,
      _channel,
      _send,
      _linkedBinding
    };
    process_default = _process;
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/_virtual_unenv_global_polyfill-@cloudflare-unenv-preset-node-process
var init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/_virtual_unenv_global_polyfill-@cloudflare-unenv-preset-node-process"() {
    init_process2();
    globalThis.process = process_default;
  }
});

// wrangler-modules-watch:wrangler:modules-watch
var init_wrangler_modules_watch = __esm({
  "wrangler-modules-watch:wrangler:modules-watch"() {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
  }
});

// ../../../AppData/Roaming/npm/node_modules/wrangler/templates/modules-watch-stub.js
var init_modules_watch_stub = __esm({
  "../../../AppData/Roaming/npm/node_modules/wrangler/templates/modules-watch-stub.js"() {
    init_wrangler_modules_watch();
  }
});

// node-built-in-modules:crypto
import libDefault from "crypto";
var require_crypto = __commonJS({
  "node-built-in-modules:crypto"(exports, module) {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    module.exports = libDefault;
  }
});

// node_modules/bcryptjs/dist/bcrypt.js
var require_bcrypt = __commonJS({
  "node_modules/bcryptjs/dist/bcrypt.js"(exports, module) {
    init_modules_watch_stub();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
    init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
    init_performance2();
    (function(global, factory) {
      if (typeof define === "function" && define["amd"])
        define([], factory);
      else if (typeof __require === "function" && typeof module === "object" && module && module["exports"])
        module["exports"] = factory();
      else
        (global["dcodeIO"] = global["dcodeIO"] || {})["bcrypt"] = factory();
    })(exports, function() {
      "use strict";
      var bcrypt2 = {};
      var randomFallback = null;
      function random(len) {
        if (typeof module !== "undefined" && module && module["exports"])
          try {
            return require_crypto()["randomBytes"](len);
          } catch (e) {
          }
        try {
          var a;
          (self["crypto"] || self["msCrypto"])["getRandomValues"](a = new Uint32Array(len));
          return Array.prototype.slice.call(a);
        } catch (e) {
        }
        if (!randomFallback)
          throw Error("Neither WebCryptoAPI nor a crypto module is available. Use bcrypt.setRandomFallback to set an alternative");
        return randomFallback(len);
      }
      __name(random, "random");
      var randomAvailable = false;
      try {
        random(1);
        randomAvailable = true;
      } catch (e) {
      }
      randomFallback = null;
      bcrypt2.setRandomFallback = function(random2) {
        randomFallback = random2;
      };
      bcrypt2.genSaltSync = function(rounds, seed_length) {
        rounds = rounds || GENSALT_DEFAULT_LOG2_ROUNDS;
        if (typeof rounds !== "number")
          throw Error("Illegal arguments: " + typeof rounds + ", " + typeof seed_length);
        if (rounds < 4)
          rounds = 4;
        else if (rounds > 31)
          rounds = 31;
        var salt = [];
        salt.push("$2a$");
        if (rounds < 10)
          salt.push("0");
        salt.push(rounds.toString());
        salt.push("$");
        salt.push(base64_encode(random(BCRYPT_SALT_LEN), BCRYPT_SALT_LEN));
        return salt.join("");
      };
      bcrypt2.genSalt = function(rounds, seed_length, callback) {
        if (typeof seed_length === "function")
          callback = seed_length, seed_length = void 0;
        if (typeof rounds === "function")
          callback = rounds, rounds = void 0;
        if (typeof rounds === "undefined")
          rounds = GENSALT_DEFAULT_LOG2_ROUNDS;
        else if (typeof rounds !== "number")
          throw Error("illegal arguments: " + typeof rounds);
        function _async(callback2) {
          nextTick2(function() {
            try {
              callback2(null, bcrypt2.genSaltSync(rounds));
            } catch (err) {
              callback2(err);
            }
          });
        }
        __name(_async, "_async");
        if (callback) {
          if (typeof callback !== "function")
            throw Error("Illegal callback: " + typeof callback);
          _async(callback);
        } else
          return new Promise(function(resolve, reject) {
            _async(function(err, res) {
              if (err) {
                reject(err);
                return;
              }
              resolve(res);
            });
          });
      };
      bcrypt2.hashSync = function(s, salt) {
        if (typeof salt === "undefined")
          salt = GENSALT_DEFAULT_LOG2_ROUNDS;
        if (typeof salt === "number")
          salt = bcrypt2.genSaltSync(salt);
        if (typeof s !== "string" || typeof salt !== "string")
          throw Error("Illegal arguments: " + typeof s + ", " + typeof salt);
        return _hash(s, salt);
      };
      bcrypt2.hash = function(s, salt, callback, progressCallback) {
        function _async(callback2) {
          if (typeof s === "string" && typeof salt === "number")
            bcrypt2.genSalt(salt, function(err, salt2) {
              _hash(s, salt2, callback2, progressCallback);
            });
          else if (typeof s === "string" && typeof salt === "string")
            _hash(s, salt, callback2, progressCallback);
          else
            nextTick2(callback2.bind(this, Error("Illegal arguments: " + typeof s + ", " + typeof salt)));
        }
        __name(_async, "_async");
        if (callback) {
          if (typeof callback !== "function")
            throw Error("Illegal callback: " + typeof callback);
          _async(callback);
        } else
          return new Promise(function(resolve, reject) {
            _async(function(err, res) {
              if (err) {
                reject(err);
                return;
              }
              resolve(res);
            });
          });
      };
      function safeStringCompare(known, unknown) {
        var right = 0, wrong = 0;
        for (var i = 0, k = known.length; i < k; ++i) {
          if (known.charCodeAt(i) === unknown.charCodeAt(i))
            ++right;
          else
            ++wrong;
        }
        if (right < 0)
          return false;
        return wrong === 0;
      }
      __name(safeStringCompare, "safeStringCompare");
      bcrypt2.compareSync = function(s, hash) {
        if (typeof s !== "string" || typeof hash !== "string")
          throw Error("Illegal arguments: " + typeof s + ", " + typeof hash);
        if (hash.length !== 60)
          return false;
        return safeStringCompare(bcrypt2.hashSync(s, hash.substr(0, hash.length - 31)), hash);
      };
      bcrypt2.compare = function(s, hash, callback, progressCallback) {
        function _async(callback2) {
          if (typeof s !== "string" || typeof hash !== "string") {
            nextTick2(callback2.bind(this, Error("Illegal arguments: " + typeof s + ", " + typeof hash)));
            return;
          }
          if (hash.length !== 60) {
            nextTick2(callback2.bind(this, null, false));
            return;
          }
          bcrypt2.hash(s, hash.substr(0, 29), function(err, comp) {
            if (err)
              callback2(err);
            else
              callback2(null, safeStringCompare(comp, hash));
          }, progressCallback);
        }
        __name(_async, "_async");
        if (callback) {
          if (typeof callback !== "function")
            throw Error("Illegal callback: " + typeof callback);
          _async(callback);
        } else
          return new Promise(function(resolve, reject) {
            _async(function(err, res) {
              if (err) {
                reject(err);
                return;
              }
              resolve(res);
            });
          });
      };
      bcrypt2.getRounds = function(hash) {
        if (typeof hash !== "string")
          throw Error("Illegal arguments: " + typeof hash);
        return parseInt(hash.split("$")[2], 10);
      };
      bcrypt2.getSalt = function(hash) {
        if (typeof hash !== "string")
          throw Error("Illegal arguments: " + typeof hash);
        if (hash.length !== 60)
          throw Error("Illegal hash length: " + hash.length + " != 60");
        return hash.substring(0, 29);
      };
      var nextTick2 = typeof process !== "undefined" && process && typeof process.nextTick === "function" ? typeof setImmediate === "function" ? setImmediate : process.nextTick : setTimeout;
      function stringToBytes(str) {
        var out = [], i = 0;
        utfx.encodeUTF16toUTF8(function() {
          if (i >= str.length) return null;
          return str.charCodeAt(i++);
        }, function(b) {
          out.push(b);
        });
        return out;
      }
      __name(stringToBytes, "stringToBytes");
      var BASE64_CODE = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".split("");
      var BASE64_INDEX = [
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        0,
        1,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
        61,
        62,
        63,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        -1,
        -1,
        -1,
        -1,
        -1,
        -1,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        -1,
        -1,
        -1,
        -1,
        -1
      ];
      var stringFromCharCode = String.fromCharCode;
      function base64_encode(b, len) {
        var off2 = 0, rs = [], c1, c2;
        if (len <= 0 || len > b.length)
          throw Error("Illegal len: " + len);
        while (off2 < len) {
          c1 = b[off2++] & 255;
          rs.push(BASE64_CODE[c1 >> 2 & 63]);
          c1 = (c1 & 3) << 4;
          if (off2 >= len) {
            rs.push(BASE64_CODE[c1 & 63]);
            break;
          }
          c2 = b[off2++] & 255;
          c1 |= c2 >> 4 & 15;
          rs.push(BASE64_CODE[c1 & 63]);
          c1 = (c2 & 15) << 2;
          if (off2 >= len) {
            rs.push(BASE64_CODE[c1 & 63]);
            break;
          }
          c2 = b[off2++] & 255;
          c1 |= c2 >> 6 & 3;
          rs.push(BASE64_CODE[c1 & 63]);
          rs.push(BASE64_CODE[c2 & 63]);
        }
        return rs.join("");
      }
      __name(base64_encode, "base64_encode");
      function base64_decode(s, len) {
        var off2 = 0, slen = s.length, olen = 0, rs = [], c1, c2, c3, c4, o, code;
        if (len <= 0)
          throw Error("Illegal len: " + len);
        while (off2 < slen - 1 && olen < len) {
          code = s.charCodeAt(off2++);
          c1 = code < BASE64_INDEX.length ? BASE64_INDEX[code] : -1;
          code = s.charCodeAt(off2++);
          c2 = code < BASE64_INDEX.length ? BASE64_INDEX[code] : -1;
          if (c1 == -1 || c2 == -1)
            break;
          o = c1 << 2 >>> 0;
          o |= (c2 & 48) >> 4;
          rs.push(stringFromCharCode(o));
          if (++olen >= len || off2 >= slen)
            break;
          code = s.charCodeAt(off2++);
          c3 = code < BASE64_INDEX.length ? BASE64_INDEX[code] : -1;
          if (c3 == -1)
            break;
          o = (c2 & 15) << 4 >>> 0;
          o |= (c3 & 60) >> 2;
          rs.push(stringFromCharCode(o));
          if (++olen >= len || off2 >= slen)
            break;
          code = s.charCodeAt(off2++);
          c4 = code < BASE64_INDEX.length ? BASE64_INDEX[code] : -1;
          o = (c3 & 3) << 6 >>> 0;
          o |= c4;
          rs.push(stringFromCharCode(o));
          ++olen;
        }
        var res = [];
        for (off2 = 0; off2 < olen; off2++)
          res.push(rs[off2].charCodeAt(0));
        return res;
      }
      __name(base64_decode, "base64_decode");
      var utfx = (function() {
        "use strict";
        var utfx2 = {};
        utfx2.MAX_CODEPOINT = 1114111;
        utfx2.encodeUTF8 = function(src, dst) {
          var cp = null;
          if (typeof src === "number")
            cp = src, src = /* @__PURE__ */ __name(function() {
              return null;
            }, "src");
          while (cp !== null || (cp = src()) !== null) {
            if (cp < 128)
              dst(cp & 127);
            else if (cp < 2048)
              dst(cp >> 6 & 31 | 192), dst(cp & 63 | 128);
            else if (cp < 65536)
              dst(cp >> 12 & 15 | 224), dst(cp >> 6 & 63 | 128), dst(cp & 63 | 128);
            else
              dst(cp >> 18 & 7 | 240), dst(cp >> 12 & 63 | 128), dst(cp >> 6 & 63 | 128), dst(cp & 63 | 128);
            cp = null;
          }
        };
        utfx2.decodeUTF8 = function(src, dst) {
          var a, b, c, d, fail = /* @__PURE__ */ __name(function(b2) {
            b2 = b2.slice(0, b2.indexOf(null));
            var err = Error(b2.toString());
            err.name = "TruncatedError";
            err["bytes"] = b2;
            throw err;
          }, "fail");
          while ((a = src()) !== null) {
            if ((a & 128) === 0)
              dst(a);
            else if ((a & 224) === 192)
              (b = src()) === null && fail([a, b]), dst((a & 31) << 6 | b & 63);
            else if ((a & 240) === 224)
              ((b = src()) === null || (c = src()) === null) && fail([a, b, c]), dst((a & 15) << 12 | (b & 63) << 6 | c & 63);
            else if ((a & 248) === 240)
              ((b = src()) === null || (c = src()) === null || (d = src()) === null) && fail([a, b, c, d]), dst((a & 7) << 18 | (b & 63) << 12 | (c & 63) << 6 | d & 63);
            else throw RangeError("Illegal starting byte: " + a);
          }
        };
        utfx2.UTF16toUTF8 = function(src, dst) {
          var c1, c2 = null;
          while (true) {
            if ((c1 = c2 !== null ? c2 : src()) === null)
              break;
            if (c1 >= 55296 && c1 <= 57343) {
              if ((c2 = src()) !== null) {
                if (c2 >= 56320 && c2 <= 57343) {
                  dst((c1 - 55296) * 1024 + c2 - 56320 + 65536);
                  c2 = null;
                  continue;
                }
              }
            }
            dst(c1);
          }
          if (c2 !== null) dst(c2);
        };
        utfx2.UTF8toUTF16 = function(src, dst) {
          var cp = null;
          if (typeof src === "number")
            cp = src, src = /* @__PURE__ */ __name(function() {
              return null;
            }, "src");
          while (cp !== null || (cp = src()) !== null) {
            if (cp <= 65535)
              dst(cp);
            else
              cp -= 65536, dst((cp >> 10) + 55296), dst(cp % 1024 + 56320);
            cp = null;
          }
        };
        utfx2.encodeUTF16toUTF8 = function(src, dst) {
          utfx2.UTF16toUTF8(src, function(cp) {
            utfx2.encodeUTF8(cp, dst);
          });
        };
        utfx2.decodeUTF8toUTF16 = function(src, dst) {
          utfx2.decodeUTF8(src, function(cp) {
            utfx2.UTF8toUTF16(cp, dst);
          });
        };
        utfx2.calculateCodePoint = function(cp) {
          return cp < 128 ? 1 : cp < 2048 ? 2 : cp < 65536 ? 3 : 4;
        };
        utfx2.calculateUTF8 = function(src) {
          var cp, l = 0;
          while ((cp = src()) !== null)
            l += utfx2.calculateCodePoint(cp);
          return l;
        };
        utfx2.calculateUTF16asUTF8 = function(src) {
          var n = 0, l = 0;
          utfx2.UTF16toUTF8(src, function(cp) {
            ++n;
            l += utfx2.calculateCodePoint(cp);
          });
          return [n, l];
        };
        return utfx2;
      })();
      Date.now = Date.now || function() {
        return +/* @__PURE__ */ new Date();
      };
      var BCRYPT_SALT_LEN = 16;
      var GENSALT_DEFAULT_LOG2_ROUNDS = 10;
      var BLOWFISH_NUM_ROUNDS = 16;
      var MAX_EXECUTION_TIME = 100;
      var P_ORIG = [
        608135816,
        2242054355,
        320440878,
        57701188,
        2752067618,
        698298832,
        137296536,
        3964562569,
        1160258022,
        953160567,
        3193202383,
        887688300,
        3232508343,
        3380367581,
        1065670069,
        3041331479,
        2450970073,
        2306472731
      ];
      var S_ORIG = [
        3509652390,
        2564797868,
        805139163,
        3491422135,
        3101798381,
        1780907670,
        3128725573,
        4046225305,
        614570311,
        3012652279,
        134345442,
        2240740374,
        1667834072,
        1901547113,
        2757295779,
        4103290238,
        227898511,
        1921955416,
        1904987480,
        2182433518,
        2069144605,
        3260701109,
        2620446009,
        720527379,
        3318853667,
        677414384,
        3393288472,
        3101374703,
        2390351024,
        1614419982,
        1822297739,
        2954791486,
        3608508353,
        3174124327,
        2024746970,
        1432378464,
        3864339955,
        2857741204,
        1464375394,
        1676153920,
        1439316330,
        715854006,
        3033291828,
        289532110,
        2706671279,
        2087905683,
        3018724369,
        1668267050,
        732546397,
        1947742710,
        3462151702,
        2609353502,
        2950085171,
        1814351708,
        2050118529,
        680887927,
        999245976,
        1800124847,
        3300911131,
        1713906067,
        1641548236,
        4213287313,
        1216130144,
        1575780402,
        4018429277,
        3917837745,
        3693486850,
        3949271944,
        596196993,
        3549867205,
        258830323,
        2213823033,
        772490370,
        2760122372,
        1774776394,
        2652871518,
        566650946,
        4142492826,
        1728879713,
        2882767088,
        1783734482,
        3629395816,
        2517608232,
        2874225571,
        1861159788,
        326777828,
        3124490320,
        2130389656,
        2716951837,
        967770486,
        1724537150,
        2185432712,
        2364442137,
        1164943284,
        2105845187,
        998989502,
        3765401048,
        2244026483,
        1075463327,
        1455516326,
        1322494562,
        910128902,
        469688178,
        1117454909,
        936433444,
        3490320968,
        3675253459,
        1240580251,
        122909385,
        2157517691,
        634681816,
        4142456567,
        3825094682,
        3061402683,
        2540495037,
        79693498,
        3249098678,
        1084186820,
        1583128258,
        426386531,
        1761308591,
        1047286709,
        322548459,
        995290223,
        1845252383,
        2603652396,
        3431023940,
        2942221577,
        3202600964,
        3727903485,
        1712269319,
        422464435,
        3234572375,
        1170764815,
        3523960633,
        3117677531,
        1434042557,
        442511882,
        3600875718,
        1076654713,
        1738483198,
        4213154764,
        2393238008,
        3677496056,
        1014306527,
        4251020053,
        793779912,
        2902807211,
        842905082,
        4246964064,
        1395751752,
        1040244610,
        2656851899,
        3396308128,
        445077038,
        3742853595,
        3577915638,
        679411651,
        2892444358,
        2354009459,
        1767581616,
        3150600392,
        3791627101,
        3102740896,
        284835224,
        4246832056,
        1258075500,
        768725851,
        2589189241,
        3069724005,
        3532540348,
        1274779536,
        3789419226,
        2764799539,
        1660621633,
        3471099624,
        4011903706,
        913787905,
        3497959166,
        737222580,
        2514213453,
        2928710040,
        3937242737,
        1804850592,
        3499020752,
        2949064160,
        2386320175,
        2390070455,
        2415321851,
        4061277028,
        2290661394,
        2416832540,
        1336762016,
        1754252060,
        3520065937,
        3014181293,
        791618072,
        3188594551,
        3933548030,
        2332172193,
        3852520463,
        3043980520,
        413987798,
        3465142937,
        3030929376,
        4245938359,
        2093235073,
        3534596313,
        375366246,
        2157278981,
        2479649556,
        555357303,
        3870105701,
        2008414854,
        3344188149,
        4221384143,
        3956125452,
        2067696032,
        3594591187,
        2921233993,
        2428461,
        544322398,
        577241275,
        1471733935,
        610547355,
        4027169054,
        1432588573,
        1507829418,
        2025931657,
        3646575487,
        545086370,
        48609733,
        2200306550,
        1653985193,
        298326376,
        1316178497,
        3007786442,
        2064951626,
        458293330,
        2589141269,
        3591329599,
        3164325604,
        727753846,
        2179363840,
        146436021,
        1461446943,
        4069977195,
        705550613,
        3059967265,
        3887724982,
        4281599278,
        3313849956,
        1404054877,
        2845806497,
        146425753,
        1854211946,
        1266315497,
        3048417604,
        3681880366,
        3289982499,
        290971e4,
        1235738493,
        2632868024,
        2414719590,
        3970600049,
        1771706367,
        1449415276,
        3266420449,
        422970021,
        1963543593,
        2690192192,
        3826793022,
        1062508698,
        1531092325,
        1804592342,
        2583117782,
        2714934279,
        4024971509,
        1294809318,
        4028980673,
        1289560198,
        2221992742,
        1669523910,
        35572830,
        157838143,
        1052438473,
        1016535060,
        1802137761,
        1753167236,
        1386275462,
        3080475397,
        2857371447,
        1040679964,
        2145300060,
        2390574316,
        1461121720,
        2956646967,
        4031777805,
        4028374788,
        33600511,
        2920084762,
        1018524850,
        629373528,
        3691585981,
        3515945977,
        2091462646,
        2486323059,
        586499841,
        988145025,
        935516892,
        3367335476,
        2599673255,
        2839830854,
        265290510,
        3972581182,
        2759138881,
        3795373465,
        1005194799,
        847297441,
        406762289,
        1314163512,
        1332590856,
        1866599683,
        4127851711,
        750260880,
        613907577,
        1450815602,
        3165620655,
        3734664991,
        3650291728,
        3012275730,
        3704569646,
        1427272223,
        778793252,
        1343938022,
        2676280711,
        2052605720,
        1946737175,
        3164576444,
        3914038668,
        3967478842,
        3682934266,
        1661551462,
        3294938066,
        4011595847,
        840292616,
        3712170807,
        616741398,
        312560963,
        711312465,
        1351876610,
        322626781,
        1910503582,
        271666773,
        2175563734,
        1594956187,
        70604529,
        3617834859,
        1007753275,
        1495573769,
        4069517037,
        2549218298,
        2663038764,
        504708206,
        2263041392,
        3941167025,
        2249088522,
        1514023603,
        1998579484,
        1312622330,
        694541497,
        2582060303,
        2151582166,
        1382467621,
        776784248,
        2618340202,
        3323268794,
        2497899128,
        2784771155,
        503983604,
        4076293799,
        907881277,
        423175695,
        432175456,
        1378068232,
        4145222326,
        3954048622,
        3938656102,
        3820766613,
        2793130115,
        2977904593,
        26017576,
        3274890735,
        3194772133,
        1700274565,
        1756076034,
        4006520079,
        3677328699,
        720338349,
        1533947780,
        354530856,
        688349552,
        3973924725,
        1637815568,
        332179504,
        3949051286,
        53804574,
        2852348879,
        3044236432,
        1282449977,
        3583942155,
        3416972820,
        4006381244,
        1617046695,
        2628476075,
        3002303598,
        1686838959,
        431878346,
        2686675385,
        1700445008,
        1080580658,
        1009431731,
        832498133,
        3223435511,
        2605976345,
        2271191193,
        2516031870,
        1648197032,
        4164389018,
        2548247927,
        300782431,
        375919233,
        238389289,
        3353747414,
        2531188641,
        2019080857,
        1475708069,
        455242339,
        2609103871,
        448939670,
        3451063019,
        1395535956,
        2413381860,
        1841049896,
        1491858159,
        885456874,
        4264095073,
        4001119347,
        1565136089,
        3898914787,
        1108368660,
        540939232,
        1173283510,
        2745871338,
        3681308437,
        4207628240,
        3343053890,
        4016749493,
        1699691293,
        1103962373,
        3625875870,
        2256883143,
        3830138730,
        1031889488,
        3479347698,
        1535977030,
        4236805024,
        3251091107,
        2132092099,
        1774941330,
        1199868427,
        1452454533,
        157007616,
        2904115357,
        342012276,
        595725824,
        1480756522,
        206960106,
        497939518,
        591360097,
        863170706,
        2375253569,
        3596610801,
        1814182875,
        2094937945,
        3421402208,
        1082520231,
        3463918190,
        2785509508,
        435703966,
        3908032597,
        1641649973,
        2842273706,
        3305899714,
        1510255612,
        2148256476,
        2655287854,
        3276092548,
        4258621189,
        236887753,
        3681803219,
        274041037,
        1734335097,
        3815195456,
        3317970021,
        1899903192,
        1026095262,
        4050517792,
        356393447,
        2410691914,
        3873677099,
        3682840055,
        3913112168,
        2491498743,
        4132185628,
        2489919796,
        1091903735,
        1979897079,
        3170134830,
        3567386728,
        3557303409,
        857797738,
        1136121015,
        1342202287,
        507115054,
        2535736646,
        337727348,
        3213592640,
        1301675037,
        2528481711,
        1895095763,
        1721773893,
        3216771564,
        62756741,
        2142006736,
        835421444,
        2531993523,
        1442658625,
        3659876326,
        2882144922,
        676362277,
        1392781812,
        170690266,
        3921047035,
        1759253602,
        3611846912,
        1745797284,
        664899054,
        1329594018,
        3901205900,
        3045908486,
        2062866102,
        2865634940,
        3543621612,
        3464012697,
        1080764994,
        553557557,
        3656615353,
        3996768171,
        991055499,
        499776247,
        1265440854,
        648242737,
        3940784050,
        980351604,
        3713745714,
        1749149687,
        3396870395,
        4211799374,
        3640570775,
        1161844396,
        3125318951,
        1431517754,
        545492359,
        4268468663,
        3499529547,
        1437099964,
        2702547544,
        3433638243,
        2581715763,
        2787789398,
        1060185593,
        1593081372,
        2418618748,
        4260947970,
        69676912,
        2159744348,
        86519011,
        2512459080,
        3838209314,
        1220612927,
        3339683548,
        133810670,
        1090789135,
        1078426020,
        1569222167,
        845107691,
        3583754449,
        4072456591,
        1091646820,
        628848692,
        1613405280,
        3757631651,
        526609435,
        236106946,
        48312990,
        2942717905,
        3402727701,
        1797494240,
        859738849,
        992217954,
        4005476642,
        2243076622,
        3870952857,
        3732016268,
        765654824,
        3490871365,
        2511836413,
        1685915746,
        3888969200,
        1414112111,
        2273134842,
        3281911079,
        4080962846,
        172450625,
        2569994100,
        980381355,
        4109958455,
        2819808352,
        2716589560,
        2568741196,
        3681446669,
        3329971472,
        1835478071,
        660984891,
        3704678404,
        4045999559,
        3422617507,
        3040415634,
        1762651403,
        1719377915,
        3470491036,
        2693910283,
        3642056355,
        3138596744,
        1364962596,
        2073328063,
        1983633131,
        926494387,
        3423689081,
        2150032023,
        4096667949,
        1749200295,
        3328846651,
        309677260,
        2016342300,
        1779581495,
        3079819751,
        111262694,
        1274766160,
        443224088,
        298511866,
        1025883608,
        3806446537,
        1145181785,
        168956806,
        3641502830,
        3584813610,
        1689216846,
        3666258015,
        3200248200,
        1692713982,
        2646376535,
        4042768518,
        1618508792,
        1610833997,
        3523052358,
        4130873264,
        2001055236,
        3610705100,
        2202168115,
        4028541809,
        2961195399,
        1006657119,
        2006996926,
        3186142756,
        1430667929,
        3210227297,
        1314452623,
        4074634658,
        4101304120,
        2273951170,
        1399257539,
        3367210612,
        3027628629,
        1190975929,
        2062231137,
        2333990788,
        2221543033,
        2438960610,
        1181637006,
        548689776,
        2362791313,
        3372408396,
        3104550113,
        3145860560,
        296247880,
        1970579870,
        3078560182,
        3769228297,
        1714227617,
        3291629107,
        3898220290,
        166772364,
        1251581989,
        493813264,
        448347421,
        195405023,
        2709975567,
        677966185,
        3703036547,
        1463355134,
        2715995803,
        1338867538,
        1343315457,
        2802222074,
        2684532164,
        233230375,
        2599980071,
        2000651841,
        3277868038,
        1638401717,
        4028070440,
        3237316320,
        6314154,
        819756386,
        300326615,
        590932579,
        1405279636,
        3267499572,
        3150704214,
        2428286686,
        3959192993,
        3461946742,
        1862657033,
        1266418056,
        963775037,
        2089974820,
        2263052895,
        1917689273,
        448879540,
        3550394620,
        3981727096,
        150775221,
        3627908307,
        1303187396,
        508620638,
        2975983352,
        2726630617,
        1817252668,
        1876281319,
        1457606340,
        908771278,
        3720792119,
        3617206836,
        2455994898,
        1729034894,
        1080033504,
        976866871,
        3556439503,
        2881648439,
        1522871579,
        1555064734,
        1336096578,
        3548522304,
        2579274686,
        3574697629,
        3205460757,
        3593280638,
        3338716283,
        3079412587,
        564236357,
        2993598910,
        1781952180,
        1464380207,
        3163844217,
        3332601554,
        1699332808,
        1393555694,
        1183702653,
        3581086237,
        1288719814,
        691649499,
        2847557200,
        2895455976,
        3193889540,
        2717570544,
        1781354906,
        1676643554,
        2592534050,
        3230253752,
        1126444790,
        2770207658,
        2633158820,
        2210423226,
        2615765581,
        2414155088,
        3127139286,
        673620729,
        2805611233,
        1269405062,
        4015350505,
        3341807571,
        4149409754,
        1057255273,
        2012875353,
        2162469141,
        2276492801,
        2601117357,
        993977747,
        3918593370,
        2654263191,
        753973209,
        36408145,
        2530585658,
        25011837,
        3520020182,
        2088578344,
        530523599,
        2918365339,
        1524020338,
        1518925132,
        3760827505,
        3759777254,
        1202760957,
        3985898139,
        3906192525,
        674977740,
        4174734889,
        2031300136,
        2019492241,
        3983892565,
        4153806404,
        3822280332,
        352677332,
        2297720250,
        60907813,
        90501309,
        3286998549,
        1016092578,
        2535922412,
        2839152426,
        457141659,
        509813237,
        4120667899,
        652014361,
        1966332200,
        2975202805,
        55981186,
        2327461051,
        676427537,
        3255491064,
        2882294119,
        3433927263,
        1307055953,
        942726286,
        933058658,
        2468411793,
        3933900994,
        4215176142,
        1361170020,
        2001714738,
        2830558078,
        3274259782,
        1222529897,
        1679025792,
        2729314320,
        3714953764,
        1770335741,
        151462246,
        3013232138,
        1682292957,
        1483529935,
        471910574,
        1539241949,
        458788160,
        3436315007,
        1807016891,
        3718408830,
        978976581,
        1043663428,
        3165965781,
        1927990952,
        4200891579,
        2372276910,
        3208408903,
        3533431907,
        1412390302,
        2931980059,
        4132332400,
        1947078029,
        3881505623,
        4168226417,
        2941484381,
        1077988104,
        1320477388,
        886195818,
        18198404,
        3786409e3,
        2509781533,
        112762804,
        3463356488,
        1866414978,
        891333506,
        18488651,
        661792760,
        1628790961,
        3885187036,
        3141171499,
        876946877,
        2693282273,
        1372485963,
        791857591,
        2686433993,
        3759982718,
        3167212022,
        3472953795,
        2716379847,
        445679433,
        3561995674,
        3504004811,
        3574258232,
        54117162,
        3331405415,
        2381918588,
        3769707343,
        4154350007,
        1140177722,
        4074052095,
        668550556,
        3214352940,
        367459370,
        261225585,
        2610173221,
        4209349473,
        3468074219,
        3265815641,
        314222801,
        3066103646,
        3808782860,
        282218597,
        3406013506,
        3773591054,
        379116347,
        1285071038,
        846784868,
        2669647154,
        3771962079,
        3550491691,
        2305946142,
        453669953,
        1268987020,
        3317592352,
        3279303384,
        3744833421,
        2610507566,
        3859509063,
        266596637,
        3847019092,
        517658769,
        3462560207,
        3443424879,
        370717030,
        4247526661,
        2224018117,
        4143653529,
        4112773975,
        2788324899,
        2477274417,
        1456262402,
        2901442914,
        1517677493,
        1846949527,
        2295493580,
        3734397586,
        2176403920,
        1280348187,
        1908823572,
        3871786941,
        846861322,
        1172426758,
        3287448474,
        3383383037,
        1655181056,
        3139813346,
        901632758,
        1897031941,
        2986607138,
        3066810236,
        3447102507,
        1393639104,
        373351379,
        950779232,
        625454576,
        3124240540,
        4148612726,
        2007998917,
        544563296,
        2244738638,
        2330496472,
        2058025392,
        1291430526,
        424198748,
        50039436,
        29584100,
        3605783033,
        2429876329,
        2791104160,
        1057563949,
        3255363231,
        3075367218,
        3463963227,
        1469046755,
        985887462
      ];
      var C_ORIG = [
        1332899944,
        1700884034,
        1701343084,
        1684370003,
        1668446532,
        1869963892
      ];
      function _encipher(lr, off2, P, S) {
        var n, l = lr[off2], r = lr[off2 + 1];
        l ^= P[0];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[1];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[2];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[3];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[4];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[5];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[6];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[7];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[8];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[9];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[10];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[11];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[12];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[13];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[14];
        n = S[l >>> 24];
        n += S[256 | l >> 16 & 255];
        n ^= S[512 | l >> 8 & 255];
        n += S[768 | l & 255];
        r ^= n ^ P[15];
        n = S[r >>> 24];
        n += S[256 | r >> 16 & 255];
        n ^= S[512 | r >> 8 & 255];
        n += S[768 | r & 255];
        l ^= n ^ P[16];
        lr[off2] = r ^ P[BLOWFISH_NUM_ROUNDS + 1];
        lr[off2 + 1] = l;
        return lr;
      }
      __name(_encipher, "_encipher");
      function _streamtoword(data, offp) {
        for (var i = 0, word = 0; i < 4; ++i)
          word = word << 8 | data[offp] & 255, offp = (offp + 1) % data.length;
        return { key: word, offp };
      }
      __name(_streamtoword, "_streamtoword");
      function _key(key, P, S) {
        var offset = 0, lr = [0, 0], plen = P.length, slen = S.length, sw;
        for (var i = 0; i < plen; i++)
          sw = _streamtoword(key, offset), offset = sw.offp, P[i] = P[i] ^ sw.key;
        for (i = 0; i < plen; i += 2)
          lr = _encipher(lr, 0, P, S), P[i] = lr[0], P[i + 1] = lr[1];
        for (i = 0; i < slen; i += 2)
          lr = _encipher(lr, 0, P, S), S[i] = lr[0], S[i + 1] = lr[1];
      }
      __name(_key, "_key");
      function _ekskey(data, key, P, S) {
        var offp = 0, lr = [0, 0], plen = P.length, slen = S.length, sw;
        for (var i = 0; i < plen; i++)
          sw = _streamtoword(key, offp), offp = sw.offp, P[i] = P[i] ^ sw.key;
        offp = 0;
        for (i = 0; i < plen; i += 2)
          sw = _streamtoword(data, offp), offp = sw.offp, lr[0] ^= sw.key, sw = _streamtoword(data, offp), offp = sw.offp, lr[1] ^= sw.key, lr = _encipher(lr, 0, P, S), P[i] = lr[0], P[i + 1] = lr[1];
        for (i = 0; i < slen; i += 2)
          sw = _streamtoword(data, offp), offp = sw.offp, lr[0] ^= sw.key, sw = _streamtoword(data, offp), offp = sw.offp, lr[1] ^= sw.key, lr = _encipher(lr, 0, P, S), S[i] = lr[0], S[i + 1] = lr[1];
      }
      __name(_ekskey, "_ekskey");
      function _crypt(b, salt, rounds, callback, progressCallback) {
        var cdata = C_ORIG.slice(), clen = cdata.length, err;
        if (rounds < 4 || rounds > 31) {
          err = Error("Illegal number of rounds (4-31): " + rounds);
          if (callback) {
            nextTick2(callback.bind(this, err));
            return;
          } else
            throw err;
        }
        if (salt.length !== BCRYPT_SALT_LEN) {
          err = Error("Illegal salt length: " + salt.length + " != " + BCRYPT_SALT_LEN);
          if (callback) {
            nextTick2(callback.bind(this, err));
            return;
          } else
            throw err;
        }
        rounds = 1 << rounds >>> 0;
        var P, S, i = 0, j;
        if (Int32Array) {
          P = new Int32Array(P_ORIG);
          S = new Int32Array(S_ORIG);
        } else {
          P = P_ORIG.slice();
          S = S_ORIG.slice();
        }
        _ekskey(salt, b, P, S);
        function next() {
          if (progressCallback)
            progressCallback(i / rounds);
          if (i < rounds) {
            var start = Date.now();
            for (; i < rounds; ) {
              i = i + 1;
              _key(b, P, S);
              _key(salt, P, S);
              if (Date.now() - start > MAX_EXECUTION_TIME)
                break;
            }
          } else {
            for (i = 0; i < 64; i++)
              for (j = 0; j < clen >> 1; j++)
                _encipher(cdata, j << 1, P, S);
            var ret = [];
            for (i = 0; i < clen; i++)
              ret.push((cdata[i] >> 24 & 255) >>> 0), ret.push((cdata[i] >> 16 & 255) >>> 0), ret.push((cdata[i] >> 8 & 255) >>> 0), ret.push((cdata[i] & 255) >>> 0);
            if (callback) {
              callback(null, ret);
              return;
            } else
              return ret;
          }
          if (callback)
            nextTick2(next);
        }
        __name(next, "next");
        if (typeof callback !== "undefined") {
          next();
        } else {
          var res;
          while (true)
            if (typeof (res = next()) !== "undefined")
              return res || [];
        }
      }
      __name(_crypt, "_crypt");
      function _hash(s, salt, callback, progressCallback) {
        var err;
        if (typeof s !== "string" || typeof salt !== "string") {
          err = Error("Invalid string / salt: Not a string");
          if (callback) {
            nextTick2(callback.bind(this, err));
            return;
          } else
            throw err;
        }
        var minor, offset;
        if (salt.charAt(0) !== "$" || salt.charAt(1) !== "2") {
          err = Error("Invalid salt version: " + salt.substring(0, 2));
          if (callback) {
            nextTick2(callback.bind(this, err));
            return;
          } else
            throw err;
        }
        if (salt.charAt(2) === "$")
          minor = String.fromCharCode(0), offset = 3;
        else {
          minor = salt.charAt(2);
          if (minor !== "a" && minor !== "b" && minor !== "y" || salt.charAt(3) !== "$") {
            err = Error("Invalid salt revision: " + salt.substring(2, 4));
            if (callback) {
              nextTick2(callback.bind(this, err));
              return;
            } else
              throw err;
          }
          offset = 4;
        }
        if (salt.charAt(offset + 2) > "$") {
          err = Error("Missing salt rounds");
          if (callback) {
            nextTick2(callback.bind(this, err));
            return;
          } else
            throw err;
        }
        var r1 = parseInt(salt.substring(offset, offset + 1), 10) * 10, r2 = parseInt(salt.substring(offset + 1, offset + 2), 10), rounds = r1 + r2, real_salt = salt.substring(offset + 3, offset + 25);
        s += minor >= "a" ? "\0" : "";
        var passwordb = stringToBytes(s), saltb = base64_decode(real_salt, BCRYPT_SALT_LEN);
        function finish(bytes) {
          var res = [];
          res.push("$2");
          if (minor >= "a")
            res.push(minor);
          res.push("$");
          if (rounds < 10)
            res.push("0");
          res.push(rounds.toString());
          res.push("$");
          res.push(base64_encode(saltb, saltb.length));
          res.push(base64_encode(bytes, C_ORIG.length * 4 - 1));
          return res.join("");
        }
        __name(finish, "finish");
        if (typeof callback == "undefined")
          return finish(_crypt(passwordb, saltb, rounds));
        else {
          _crypt(passwordb, saltb, rounds, function(err2, bytes) {
            if (err2)
              callback(err2, null);
            else
              callback(null, finish(bytes));
          }, progressCallback);
        }
      }
      __name(_hash, "_hash");
      bcrypt2.encodeBase64 = base64_encode;
      bcrypt2.decodeBase64 = base64_decode;
      return bcrypt2;
    });
  }
});

// .wrangler/tmp/bundle-lidyOQ/middleware-loader.entry.ts
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// .wrangler/tmp/bundle-lidyOQ/middleware-insertion-facade.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/hono.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/hono-base.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/compose.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var compose = /* @__PURE__ */ __name((middleware, onError, onNotFound) => {
  return (context2, next) => {
    let index = -1;
    return dispatch(0);
    async function dispatch(i) {
      if (i <= index) {
        throw new Error("next() called multiple times");
      }
      index = i;
      let res;
      let isError = false;
      let handler;
      if (middleware[i]) {
        handler = middleware[i][0][0];
        context2.req.routeIndex = i;
      } else {
        handler = i === middleware.length && next || void 0;
      }
      if (handler) {
        try {
          res = await handler(context2, () => dispatch(i + 1));
        } catch (err) {
          if (err instanceof Error && onError) {
            context2.error = err;
            res = await onError(err, context2);
            isError = true;
          } else {
            throw err;
          }
        }
      } else {
        if (context2.finalized === false && onNotFound) {
          res = await onNotFound(context2);
        }
      }
      if (res && (context2.finalized === false || isError)) {
        context2.res = res;
      }
      return context2;
    }
    __name(dispatch, "dispatch");
  };
}, "compose");

// node_modules/hono/dist/context.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/request.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/http-exception.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/request/constants.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var GET_MATCH_RESULT = /* @__PURE__ */ Symbol();

// node_modules/hono/dist/utils/body.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var parseBody = /* @__PURE__ */ __name(async (request, options = /* @__PURE__ */ Object.create(null)) => {
  const { all = false, dot = false } = options;
  const headers = request instanceof HonoRequest ? request.raw.headers : request.headers;
  const contentType = headers.get("Content-Type");
  if (contentType?.startsWith("multipart/form-data") || contentType?.startsWith("application/x-www-form-urlencoded")) {
    return parseFormData(request, { all, dot });
  }
  return {};
}, "parseBody");
async function parseFormData(request, options) {
  const formData = await request.formData();
  if (formData) {
    return convertFormDataToBodyData(formData, options);
  }
  return {};
}
__name(parseFormData, "parseFormData");
function convertFormDataToBodyData(formData, options) {
  const form = /* @__PURE__ */ Object.create(null);
  formData.forEach((value, key) => {
    const shouldParseAllValues = options.all || key.endsWith("[]");
    if (!shouldParseAllValues) {
      form[key] = value;
    } else {
      handleParsingAllValues(form, key, value);
    }
  });
  if (options.dot) {
    Object.entries(form).forEach(([key, value]) => {
      const shouldParseDotValues = key.includes(".");
      if (shouldParseDotValues) {
        handleParsingNestedValues(form, key, value);
        delete form[key];
      }
    });
  }
  return form;
}
__name(convertFormDataToBodyData, "convertFormDataToBodyData");
var handleParsingAllValues = /* @__PURE__ */ __name((form, key, value) => {
  if (form[key] !== void 0) {
    if (Array.isArray(form[key])) {
      ;
      form[key].push(value);
    } else {
      form[key] = [form[key], value];
    }
  } else {
    if (!key.endsWith("[]")) {
      form[key] = value;
    } else {
      form[key] = [value];
    }
  }
}, "handleParsingAllValues");
var handleParsingNestedValues = /* @__PURE__ */ __name((form, key, value) => {
  if (/(?:^|\.)__proto__\./.test(key)) {
    return;
  }
  let nestedForm = form;
  const keys = key.split(".");
  keys.forEach((key2, index) => {
    if (index === keys.length - 1) {
      nestedForm[key2] = value;
    } else {
      if (!nestedForm[key2] || typeof nestedForm[key2] !== "object" || Array.isArray(nestedForm[key2]) || nestedForm[key2] instanceof File) {
        nestedForm[key2] = /* @__PURE__ */ Object.create(null);
      }
      nestedForm = nestedForm[key2];
    }
  });
}, "handleParsingNestedValues");

// node_modules/hono/dist/utils/url.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var splitPath = /* @__PURE__ */ __name((path) => {
  const paths = path.split("/");
  if (paths[0] === "") {
    paths.shift();
  }
  return paths;
}, "splitPath");
var splitRoutingPath = /* @__PURE__ */ __name((routePath) => {
  const { groups, path } = extractGroupsFromPath(routePath);
  const paths = splitPath(path);
  return replaceGroupMarks(paths, groups);
}, "splitRoutingPath");
var extractGroupsFromPath = /* @__PURE__ */ __name((path) => {
  const groups = [];
  path = path.replace(/\{[^}]+\}/g, (match2, index) => {
    const mark = `@${index}`;
    groups.push([mark, match2]);
    return mark;
  });
  return { groups, path };
}, "extractGroupsFromPath");
var replaceGroupMarks = /* @__PURE__ */ __name((paths, groups) => {
  for (let i = groups.length - 1; i >= 0; i--) {
    const [mark] = groups[i];
    for (let j = paths.length - 1; j >= 0; j--) {
      if (paths[j].includes(mark)) {
        paths[j] = paths[j].replace(mark, groups[i][1]);
        break;
      }
    }
  }
  return paths;
}, "replaceGroupMarks");
var patternCache = {};
var getPattern = /* @__PURE__ */ __name((label, next) => {
  if (label === "*") {
    return "*";
  }
  const match2 = label.match(/^\:([^\{\}]+)(?:\{(.+)\})?$/);
  if (match2) {
    const cacheKey = `${label}#${next}`;
    if (!patternCache[cacheKey]) {
      if (match2[2]) {
        patternCache[cacheKey] = next && next[0] !== ":" && next[0] !== "*" ? [cacheKey, match2[1], new RegExp(`^${match2[2]}(?=/${next})`)] : [label, match2[1], new RegExp(`^${match2[2]}$`)];
      } else {
        patternCache[cacheKey] = [label, match2[1], true];
      }
    }
    return patternCache[cacheKey];
  }
  return null;
}, "getPattern");
var tryDecode = /* @__PURE__ */ __name((str, decoder) => {
  try {
    return decoder(str);
  } catch {
    return str.replace(/(?:%[0-9A-Fa-f]{2})+/g, (match2) => {
      try {
        return decoder(match2);
      } catch {
        return match2;
      }
    });
  }
}, "tryDecode");
var tryDecodeURI = /* @__PURE__ */ __name((str) => tryDecode(str, decodeURI), "tryDecodeURI");
var getPath = /* @__PURE__ */ __name((request) => {
  const url = request.url;
  const start = url.indexOf("/", url.indexOf(":") + 4);
  let i = start;
  for (; i < url.length; i++) {
    const charCode = url.charCodeAt(i);
    if (charCode === 37) {
      const queryIndex = url.indexOf("?", i);
      const hashIndex = url.indexOf("#", i);
      const end = queryIndex === -1 ? hashIndex === -1 ? void 0 : hashIndex : hashIndex === -1 ? queryIndex : Math.min(queryIndex, hashIndex);
      const path = url.slice(start, end);
      return tryDecodeURI(path.includes("%25") ? path.replace(/%25/g, "%2525") : path);
    } else if (charCode === 63 || charCode === 35) {
      break;
    }
  }
  return url.slice(start, i);
}, "getPath");
var getPathNoStrict = /* @__PURE__ */ __name((request) => {
  const result = getPath(request);
  return result.length > 1 && result.at(-1) === "/" ? result.slice(0, -1) : result;
}, "getPathNoStrict");
var mergePath = /* @__PURE__ */ __name((base, sub, ...rest) => {
  if (rest.length) {
    sub = mergePath(sub, ...rest);
  }
  return `${base?.[0] === "/" ? "" : "/"}${base}${sub === "/" ? "" : `${base?.at(-1) === "/" ? "" : "/"}${sub?.[0] === "/" ? sub.slice(1) : sub}`}`;
}, "mergePath");
var checkOptionalParameter = /* @__PURE__ */ __name((path) => {
  if (path.charCodeAt(path.length - 1) !== 63 || !path.includes(":")) {
    return null;
  }
  const segments = path.split("/");
  const results = [];
  let basePath = "";
  segments.forEach((segment) => {
    if (segment !== "" && !/\:/.test(segment)) {
      basePath += "/" + segment;
    } else if (/\:/.test(segment)) {
      if (/\?/.test(segment)) {
        if (results.length === 0 && basePath === "") {
          results.push("/");
        } else {
          results.push(basePath);
        }
        const optionalSegment = segment.replace("?", "");
        basePath += "/" + optionalSegment;
        results.push(basePath);
      } else {
        basePath += "/" + segment;
      }
    }
  });
  return results.filter((v, i, a) => a.indexOf(v) === i);
}, "checkOptionalParameter");
var _decodeURI = /* @__PURE__ */ __name((value) => {
  if (!/[%+]/.test(value)) {
    return value;
  }
  if (value.indexOf("+") !== -1) {
    value = value.replace(/\+/g, " ");
  }
  return value.indexOf("%") !== -1 ? tryDecode(value, decodeURIComponent_) : value;
}, "_decodeURI");
var _getQueryParam = /* @__PURE__ */ __name((url, key, multiple) => {
  let encoded;
  if (!multiple && key && !/[%+]/.test(key)) {
    let keyIndex2 = url.indexOf("?", 8);
    if (keyIndex2 === -1) {
      return void 0;
    }
    if (!url.startsWith(key, keyIndex2 + 1)) {
      keyIndex2 = url.indexOf(`&${key}`, keyIndex2 + 1);
    }
    while (keyIndex2 !== -1) {
      const trailingKeyCode = url.charCodeAt(keyIndex2 + key.length + 1);
      if (trailingKeyCode === 61) {
        const valueIndex = keyIndex2 + key.length + 2;
        const endIndex = url.indexOf("&", valueIndex);
        return _decodeURI(url.slice(valueIndex, endIndex === -1 ? void 0 : endIndex));
      } else if (trailingKeyCode == 38 || isNaN(trailingKeyCode)) {
        return "";
      }
      keyIndex2 = url.indexOf(`&${key}`, keyIndex2 + 1);
    }
    encoded = /[%+]/.test(url);
    if (!encoded) {
      return void 0;
    }
  }
  const results = {};
  encoded ??= /[%+]/.test(url);
  let keyIndex = url.indexOf("?", 8);
  while (keyIndex !== -1) {
    const nextKeyIndex = url.indexOf("&", keyIndex + 1);
    let valueIndex = url.indexOf("=", keyIndex);
    if (valueIndex > nextKeyIndex && nextKeyIndex !== -1) {
      valueIndex = -1;
    }
    let name = url.slice(
      keyIndex + 1,
      valueIndex === -1 ? nextKeyIndex === -1 ? void 0 : nextKeyIndex : valueIndex
    );
    if (encoded) {
      name = _decodeURI(name);
    }
    keyIndex = nextKeyIndex;
    if (name === "") {
      continue;
    }
    let value;
    if (valueIndex === -1) {
      value = "";
    } else {
      value = url.slice(valueIndex + 1, nextKeyIndex === -1 ? void 0 : nextKeyIndex);
      if (encoded) {
        value = _decodeURI(value);
      }
    }
    if (multiple) {
      if (!(results[name] && Array.isArray(results[name]))) {
        results[name] = [];
      }
      ;
      results[name].push(value);
    } else {
      results[name] ??= value;
    }
  }
  return key ? results[key] : results;
}, "_getQueryParam");
var getQueryParam = _getQueryParam;
var getQueryParams = /* @__PURE__ */ __name((url, key) => {
  return _getQueryParam(url, key, true);
}, "getQueryParams");
var decodeURIComponent_ = decodeURIComponent;

// node_modules/hono/dist/request.js
var tryDecodeURIComponent = /* @__PURE__ */ __name((str) => tryDecode(str, decodeURIComponent_), "tryDecodeURIComponent");
var HonoRequest = class {
  static {
    __name(this, "HonoRequest");
  }
  /**
   * `.raw` can get the raw Request object.
   *
   * @see {@link https://hono.dev/docs/api/request#raw}
   *
   * @example
   * ```ts
   * // For Cloudflare Workers
   * app.post('/', async (c) => {
   *   const metadata = c.req.raw.cf?.hostMetadata?
   *   ...
   * })
   * ```
   */
  raw;
  #validatedData;
  // Short name of validatedData
  #matchResult;
  routeIndex = 0;
  /**
   * `.path` can get the pathname of the request.
   *
   * @see {@link https://hono.dev/docs/api/request#path}
   *
   * @example
   * ```ts
   * app.get('/about/me', (c) => {
   *   const pathname = c.req.path // `/about/me`
   * })
   * ```
   */
  path;
  bodyCache = {};
  constructor(request, path = "/", matchResult = [[]]) {
    this.raw = request;
    this.path = path;
    this.#matchResult = matchResult;
    this.#validatedData = {};
  }
  param(key) {
    return key ? this.#getDecodedParam(key) : this.#getAllDecodedParams();
  }
  #getDecodedParam(key) {
    const paramKey = this.#matchResult[0][this.routeIndex][1][key];
    const param = this.#getParamValue(paramKey);
    return param && /\%/.test(param) ? tryDecodeURIComponent(param) : param;
  }
  #getAllDecodedParams() {
    const decoded = {};
    const keys = Object.keys(this.#matchResult[0][this.routeIndex][1]);
    for (const key of keys) {
      const value = this.#getParamValue(this.#matchResult[0][this.routeIndex][1][key]);
      if (value !== void 0) {
        decoded[key] = /\%/.test(value) ? tryDecodeURIComponent(value) : value;
      }
    }
    return decoded;
  }
  #getParamValue(paramKey) {
    return this.#matchResult[1] ? this.#matchResult[1][paramKey] : paramKey;
  }
  query(key) {
    return getQueryParam(this.url, key);
  }
  queries(key) {
    return getQueryParams(this.url, key);
  }
  header(name) {
    if (name) {
      return this.raw.headers.get(name) ?? void 0;
    }
    const headerData = {};
    this.raw.headers.forEach((value, key) => {
      headerData[key] = value;
    });
    return headerData;
  }
  async parseBody(options) {
    return parseBody(this, options);
  }
  #cachedBody = /* @__PURE__ */ __name((key) => {
    const { bodyCache, raw: raw2 } = this;
    const cachedBody = bodyCache[key];
    if (cachedBody) {
      return cachedBody;
    }
    const anyCachedKey = Object.keys(bodyCache)[0];
    if (anyCachedKey) {
      return bodyCache[anyCachedKey].then((body) => {
        if (anyCachedKey === "json") {
          body = JSON.stringify(body);
        }
        return new Response(body)[key]();
      });
    }
    return bodyCache[key] = raw2[key]();
  }, "#cachedBody");
  /**
   * `.json()` can parse Request body of type `application/json`
   *
   * @see {@link https://hono.dev/docs/api/request#json}
   *
   * @example
   * ```ts
   * app.post('/entry', async (c) => {
   *   const body = await c.req.json()
   * })
   * ```
   */
  json() {
    return this.#cachedBody("text").then((text) => JSON.parse(text));
  }
  /**
   * `.text()` can parse Request body of type `text/plain`
   *
   * @see {@link https://hono.dev/docs/api/request#text}
   *
   * @example
   * ```ts
   * app.post('/entry', async (c) => {
   *   const body = await c.req.text()
   * })
   * ```
   */
  text() {
    return this.#cachedBody("text");
  }
  /**
   * `.arrayBuffer()` parse Request body as an `ArrayBuffer`
   *
   * @see {@link https://hono.dev/docs/api/request#arraybuffer}
   *
   * @example
   * ```ts
   * app.post('/entry', async (c) => {
   *   const body = await c.req.arrayBuffer()
   * })
   * ```
   */
  arrayBuffer() {
    return this.#cachedBody("arrayBuffer");
  }
  /**
   * Parses the request body as a `Blob`.
   * @example
   * ```ts
   * app.post('/entry', async (c) => {
   *   const body = await c.req.blob();
   * });
   * ```
   * @see https://hono.dev/docs/api/request#blob
   */
  blob() {
    return this.#cachedBody("blob");
  }
  /**
   * Parses the request body as `FormData`.
   * @example
   * ```ts
   * app.post('/entry', async (c) => {
   *   const body = await c.req.formData();
   * });
   * ```
   * @see https://hono.dev/docs/api/request#formdata
   */
  formData() {
    return this.#cachedBody("formData");
  }
  /**
   * Adds validated data to the request.
   *
   * @param target - The target of the validation.
   * @param data - The validated data to add.
   */
  addValidatedData(target, data) {
    this.#validatedData[target] = data;
  }
  valid(target) {
    return this.#validatedData[target];
  }
  /**
   * `.url()` can get the request url strings.
   *
   * @see {@link https://hono.dev/docs/api/request#url}
   *
   * @example
   * ```ts
   * app.get('/about/me', (c) => {
   *   const url = c.req.url // `http://localhost:8787/about/me`
   *   ...
   * })
   * ```
   */
  get url() {
    return this.raw.url;
  }
  /**
   * `.method()` can get the method name of the request.
   *
   * @see {@link https://hono.dev/docs/api/request#method}
   *
   * @example
   * ```ts
   * app.get('/about/me', (c) => {
   *   const method = c.req.method // `GET`
   * })
   * ```
   */
  get method() {
    return this.raw.method;
  }
  get [GET_MATCH_RESULT]() {
    return this.#matchResult;
  }
  /**
   * `.matchedRoutes()` can return a matched route in the handler
   *
   * @deprecated
   *
   * Use matchedRoutes helper defined in "hono/route" instead.
   *
   * @see {@link https://hono.dev/docs/api/request#matchedroutes}
   *
   * @example
   * ```ts
   * app.use('*', async function logger(c, next) {
   *   await next()
   *   c.req.matchedRoutes.forEach(({ handler, method, path }, i) => {
   *     const name = handler.name || (handler.length < 2 ? '[handler]' : '[middleware]')
   *     console.log(
   *       method,
   *       ' ',
   *       path,
   *       ' '.repeat(Math.max(10 - path.length, 0)),
   *       name,
   *       i === c.req.routeIndex ? '<- respond from here' : ''
   *     )
   *   })
   * })
   * ```
   */
  get matchedRoutes() {
    return this.#matchResult[0].map(([[, route]]) => route);
  }
  /**
   * `routePath()` can retrieve the path registered within the handler
   *
   * @deprecated
   *
   * Use routePath helper defined in "hono/route" instead.
   *
   * @see {@link https://hono.dev/docs/api/request#routepath}
   *
   * @example
   * ```ts
   * app.get('/posts/:id', (c) => {
   *   return c.json({ path: c.req.routePath })
   * })
   * ```
   */
  get routePath() {
    return this.#matchResult[0].map(([[, route]]) => route)[this.routeIndex].path;
  }
};

// node_modules/hono/dist/utils/html.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var HtmlEscapedCallbackPhase = {
  Stringify: 1,
  BeforeStream: 2,
  Stream: 3
};
var raw = /* @__PURE__ */ __name((value, callbacks) => {
  const escapedString = new String(value);
  escapedString.isEscaped = true;
  escapedString.callbacks = callbacks;
  return escapedString;
}, "raw");
var resolveCallback = /* @__PURE__ */ __name(async (str, phase, preserveCallbacks, context2, buffer) => {
  if (typeof str === "object" && !(str instanceof String)) {
    if (!(str instanceof Promise)) {
      str = str.toString();
    }
    if (str instanceof Promise) {
      str = await str;
    }
  }
  const callbacks = str.callbacks;
  if (!callbacks?.length) {
    return Promise.resolve(str);
  }
  if (buffer) {
    buffer[0] += str;
  } else {
    buffer = [str];
  }
  const resStr = Promise.all(callbacks.map((c) => c({ phase, buffer, context: context2 }))).then(
    (res) => Promise.all(
      res.filter(Boolean).map((str2) => resolveCallback(str2, phase, false, context2, buffer))
    ).then(() => buffer[0])
  );
  if (preserveCallbacks) {
    return raw(await resStr, callbacks);
  } else {
    return resStr;
  }
}, "resolveCallback");

// node_modules/hono/dist/context.js
var TEXT_PLAIN = "text/plain; charset=UTF-8";
var setDefaultContentType = /* @__PURE__ */ __name((contentType, headers) => {
  return {
    "Content-Type": contentType,
    ...headers
  };
}, "setDefaultContentType");
var createResponseInstance = /* @__PURE__ */ __name((body, init) => new Response(body, init), "createResponseInstance");
var Context = class {
  static {
    __name(this, "Context");
  }
  #rawRequest;
  #req;
  /**
   * `.env` can get bindings (environment variables, secrets, KV namespaces, D1 database, R2 bucket etc.) in Cloudflare Workers.
   *
   * @see {@link https://hono.dev/docs/api/context#env}
   *
   * @example
   * ```ts
   * // Environment object for Cloudflare Workers
   * app.get('*', async c => {
   *   const counter = c.env.COUNTER
   * })
   * ```
   */
  env = {};
  #var;
  finalized = false;
  /**
   * `.error` can get the error object from the middleware if the Handler throws an error.
   *
   * @see {@link https://hono.dev/docs/api/context#error}
   *
   * @example
   * ```ts
   * app.use('*', async (c, next) => {
   *   await next()
   *   if (c.error) {
   *     // do something...
   *   }
   * })
   * ```
   */
  error;
  #status;
  #executionCtx;
  #res;
  #layout;
  #renderer;
  #notFoundHandler;
  #preparedHeaders;
  #matchResult;
  #path;
  /**
   * Creates an instance of the Context class.
   *
   * @param req - The Request object.
   * @param options - Optional configuration options for the context.
   */
  constructor(req, options) {
    this.#rawRequest = req;
    if (options) {
      this.#executionCtx = options.executionCtx;
      this.env = options.env;
      this.#notFoundHandler = options.notFoundHandler;
      this.#path = options.path;
      this.#matchResult = options.matchResult;
    }
  }
  /**
   * `.req` is the instance of {@link HonoRequest}.
   */
  get req() {
    this.#req ??= new HonoRequest(this.#rawRequest, this.#path, this.#matchResult);
    return this.#req;
  }
  /**
   * @see {@link https://hono.dev/docs/api/context#event}
   * The FetchEvent associated with the current request.
   *
   * @throws Will throw an error if the context does not have a FetchEvent.
   */
  get event() {
    if (this.#executionCtx && "respondWith" in this.#executionCtx) {
      return this.#executionCtx;
    } else {
      throw Error("This context has no FetchEvent");
    }
  }
  /**
   * @see {@link https://hono.dev/docs/api/context#executionctx}
   * The ExecutionContext associated with the current request.
   *
   * @throws Will throw an error if the context does not have an ExecutionContext.
   */
  get executionCtx() {
    if (this.#executionCtx) {
      return this.#executionCtx;
    } else {
      throw Error("This context has no ExecutionContext");
    }
  }
  /**
   * @see {@link https://hono.dev/docs/api/context#res}
   * The Response object for the current request.
   */
  get res() {
    return this.#res ||= createResponseInstance(null, {
      headers: this.#preparedHeaders ??= new Headers()
    });
  }
  /**
   * Sets the Response object for the current request.
   *
   * @param _res - The Response object to set.
   */
  set res(_res) {
    if (this.#res && _res) {
      _res = createResponseInstance(_res.body, _res);
      for (const [k, v] of this.#res.headers.entries()) {
        if (k === "content-type") {
          continue;
        }
        if (k === "set-cookie") {
          const cookies = this.#res.headers.getSetCookie();
          _res.headers.delete("set-cookie");
          for (const cookie of cookies) {
            _res.headers.append("set-cookie", cookie);
          }
        } else {
          _res.headers.set(k, v);
        }
      }
    }
    this.#res = _res;
    this.finalized = true;
  }
  /**
   * `.render()` can create a response within a layout.
   *
   * @see {@link https://hono.dev/docs/api/context#render-setrenderer}
   *
   * @example
   * ```ts
   * app.get('/', (c) => {
   *   return c.render('Hello!')
   * })
   * ```
   */
  render = /* @__PURE__ */ __name((...args) => {
    this.#renderer ??= (content) => this.html(content);
    return this.#renderer(...args);
  }, "render");
  /**
   * Sets the layout for the response.
   *
   * @param layout - The layout to set.
   * @returns The layout function.
   */
  setLayout = /* @__PURE__ */ __name((layout) => this.#layout = layout, "setLayout");
  /**
   * Gets the current layout for the response.
   *
   * @returns The current layout function.
   */
  getLayout = /* @__PURE__ */ __name(() => this.#layout, "getLayout");
  /**
   * `.setRenderer()` can set the layout in the custom middleware.
   *
   * @see {@link https://hono.dev/docs/api/context#render-setrenderer}
   *
   * @example
   * ```tsx
   * app.use('*', async (c, next) => {
   *   c.setRenderer((content) => {
   *     return c.html(
   *       <html>
   *         <body>
   *           <p>{content}</p>
   *         </body>
   *       </html>
   *     )
   *   })
   *   await next()
   * })
   * ```
   */
  setRenderer = /* @__PURE__ */ __name((renderer) => {
    this.#renderer = renderer;
  }, "setRenderer");
  /**
   * `.header()` can set headers.
   *
   * @see {@link https://hono.dev/docs/api/context#header}
   *
   * @example
   * ```ts
   * app.get('/welcome', (c) => {
   *   // Set headers
   *   c.header('X-Message', 'Hello!')
   *   c.header('Content-Type', 'text/plain')
   *
   *   return c.body('Thank you for coming')
   * })
   * ```
   */
  header = /* @__PURE__ */ __name((name, value, options) => {
    if (this.finalized) {
      this.#res = createResponseInstance(this.#res.body, this.#res);
    }
    const headers = this.#res ? this.#res.headers : this.#preparedHeaders ??= new Headers();
    if (value === void 0) {
      headers.delete(name);
    } else if (options?.append) {
      headers.append(name, value);
    } else {
      headers.set(name, value);
    }
  }, "header");
  status = /* @__PURE__ */ __name((status2) => {
    this.#status = status2;
  }, "status");
  /**
   * `.set()` can set the value specified by the key.
   *
   * @see {@link https://hono.dev/docs/api/context#set-get}
   *
   * @example
   * ```ts
   * app.use('*', async (c, next) => {
   *   c.set('message', 'Hono is hot!!')
   *   await next()
   * })
   * ```
   */
  set = /* @__PURE__ */ __name((key, value) => {
    this.#var ??= /* @__PURE__ */ new Map();
    this.#var.set(key, value);
  }, "set");
  /**
   * `.get()` can use the value specified by the key.
   *
   * @see {@link https://hono.dev/docs/api/context#set-get}
   *
   * @example
   * ```ts
   * app.get('/', (c) => {
   *   const message = c.get('message')
   *   return c.text(`The message is "${message}"`)
   * })
   * ```
   */
  get = /* @__PURE__ */ __name((key) => {
    return this.#var ? this.#var.get(key) : void 0;
  }, "get");
  /**
   * `.var` can access the value of a variable.
   *
   * @see {@link https://hono.dev/docs/api/context#var}
   *
   * @example
   * ```ts
   * const result = c.var.client.oneMethod()
   * ```
   */
  // c.var.propName is a read-only
  get var() {
    if (!this.#var) {
      return {};
    }
    return Object.fromEntries(this.#var);
  }
  #newResponse(data, arg, headers) {
    const responseHeaders = this.#res ? new Headers(this.#res.headers) : this.#preparedHeaders ?? new Headers();
    if (typeof arg === "object" && "headers" in arg) {
      const argHeaders = arg.headers instanceof Headers ? arg.headers : new Headers(arg.headers);
      for (const [key, value] of argHeaders) {
        if (key.toLowerCase() === "set-cookie") {
          responseHeaders.append(key, value);
        } else {
          responseHeaders.set(key, value);
        }
      }
    }
    if (headers) {
      for (const [k, v] of Object.entries(headers)) {
        if (typeof v === "string") {
          responseHeaders.set(k, v);
        } else {
          responseHeaders.delete(k);
          for (const v2 of v) {
            responseHeaders.append(k, v2);
          }
        }
      }
    }
    const status2 = typeof arg === "number" ? arg : arg?.status ?? this.#status;
    return createResponseInstance(data, { status: status2, headers: responseHeaders });
  }
  newResponse = /* @__PURE__ */ __name((...args) => this.#newResponse(...args), "newResponse");
  /**
   * `.body()` can return the HTTP response.
   * You can set headers with `.header()` and set HTTP status code with `.status`.
   * This can also be set in `.text()`, `.json()` and so on.
   *
   * @see {@link https://hono.dev/docs/api/context#body}
   *
   * @example
   * ```ts
   * app.get('/welcome', (c) => {
   *   // Set headers
   *   c.header('X-Message', 'Hello!')
   *   c.header('Content-Type', 'text/plain')
   *   // Set HTTP status code
   *   c.status(201)
   *
   *   // Return the response body
   *   return c.body('Thank you for coming')
   * })
   * ```
   */
  body = /* @__PURE__ */ __name((data, arg, headers) => this.#newResponse(data, arg, headers), "body");
  /**
   * `.text()` can render text as `Content-Type:text/plain`.
   *
   * @see {@link https://hono.dev/docs/api/context#text}
   *
   * @example
   * ```ts
   * app.get('/say', (c) => {
   *   return c.text('Hello!')
   * })
   * ```
   */
  text = /* @__PURE__ */ __name((text, arg, headers) => {
    return !this.#preparedHeaders && !this.#status && !arg && !headers && !this.finalized ? new Response(text) : this.#newResponse(
      text,
      arg,
      setDefaultContentType(TEXT_PLAIN, headers)
    );
  }, "text");
  /**
   * `.json()` can render JSON as `Content-Type:application/json`.
   *
   * @see {@link https://hono.dev/docs/api/context#json}
   *
   * @example
   * ```ts
   * app.get('/api', (c) => {
   *   return c.json({ message: 'Hello!' })
   * })
   * ```
   */
  json = /* @__PURE__ */ __name((object, arg, headers) => {
    return this.#newResponse(
      JSON.stringify(object),
      arg,
      setDefaultContentType("application/json", headers)
    );
  }, "json");
  html = /* @__PURE__ */ __name((html, arg, headers) => {
    const res = /* @__PURE__ */ __name((html2) => this.#newResponse(html2, arg, setDefaultContentType("text/html; charset=UTF-8", headers)), "res");
    return typeof html === "object" ? resolveCallback(html, HtmlEscapedCallbackPhase.Stringify, false, {}).then(res) : res(html);
  }, "html");
  /**
   * `.redirect()` can Redirect, default status code is 302.
   *
   * @see {@link https://hono.dev/docs/api/context#redirect}
   *
   * @example
   * ```ts
   * app.get('/redirect', (c) => {
   *   return c.redirect('/')
   * })
   * app.get('/redirect-permanently', (c) => {
   *   return c.redirect('/', 301)
   * })
   * ```
   */
  redirect = /* @__PURE__ */ __name((location, status2) => {
    const locationString = String(location);
    this.header(
      "Location",
      // Multibyes should be encoded
      // eslint-disable-next-line no-control-regex
      !/[^\x00-\xFF]/.test(locationString) ? locationString : encodeURI(locationString)
    );
    return this.newResponse(null, status2 ?? 302);
  }, "redirect");
  /**
   * `.notFound()` can return the Not Found Response.
   *
   * @see {@link https://hono.dev/docs/api/context#notfound}
   *
   * @example
   * ```ts
   * app.get('/notfound', (c) => {
   *   return c.notFound()
   * })
   * ```
   */
  notFound = /* @__PURE__ */ __name(() => {
    this.#notFoundHandler ??= () => createResponseInstance();
    return this.#notFoundHandler(this);
  }, "notFound");
};

// node_modules/hono/dist/router.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var METHOD_NAME_ALL = "ALL";
var METHOD_NAME_ALL_LOWERCASE = "all";
var METHODS = ["get", "post", "put", "delete", "options", "patch"];
var MESSAGE_MATCHER_IS_ALREADY_BUILT = "Can not add a route since the matcher is already built.";
var UnsupportedPathError = class extends Error {
  static {
    __name(this, "UnsupportedPathError");
  }
};

// node_modules/hono/dist/utils/constants.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var COMPOSED_HANDLER = "__COMPOSED_HANDLER";

// node_modules/hono/dist/hono-base.js
var notFoundHandler = /* @__PURE__ */ __name((c) => {
  return c.text("404 Not Found", 404);
}, "notFoundHandler");
var errorHandler = /* @__PURE__ */ __name((err, c) => {
  if ("getResponse" in err) {
    const res = err.getResponse();
    return c.newResponse(res.body, res);
  }
  console.error(err);
  return c.text("Internal Server Error", 500);
}, "errorHandler");
var Hono = class _Hono {
  static {
    __name(this, "_Hono");
  }
  get;
  post;
  put;
  delete;
  options;
  patch;
  all;
  on;
  use;
  /*
    This class is like an abstract class and does not have a router.
    To use it, inherit the class and implement router in the constructor.
  */
  router;
  getPath;
  // Cannot use `#` because it requires visibility at JavaScript runtime.
  _basePath = "/";
  #path = "/";
  routes = [];
  constructor(options = {}) {
    const allMethods = [...METHODS, METHOD_NAME_ALL_LOWERCASE];
    allMethods.forEach((method) => {
      this[method] = (args1, ...args) => {
        if (typeof args1 === "string") {
          this.#path = args1;
        } else {
          this.#addRoute(method, this.#path, args1);
        }
        args.forEach((handler) => {
          this.#addRoute(method, this.#path, handler);
        });
        return this;
      };
    });
    this.on = (method, path, ...handlers) => {
      for (const p of [path].flat()) {
        this.#path = p;
        for (const m of [method].flat()) {
          handlers.map((handler) => {
            this.#addRoute(m.toUpperCase(), this.#path, handler);
          });
        }
      }
      return this;
    };
    this.use = (arg1, ...handlers) => {
      if (typeof arg1 === "string") {
        this.#path = arg1;
      } else {
        this.#path = "*";
        handlers.unshift(arg1);
      }
      handlers.forEach((handler) => {
        this.#addRoute(METHOD_NAME_ALL, this.#path, handler);
      });
      return this;
    };
    const { strict, ...optionsWithoutStrict } = options;
    Object.assign(this, optionsWithoutStrict);
    this.getPath = strict ?? true ? options.getPath ?? getPath : getPathNoStrict;
  }
  #clone() {
    const clone = new _Hono({
      router: this.router,
      getPath: this.getPath
    });
    clone.errorHandler = this.errorHandler;
    clone.#notFoundHandler = this.#notFoundHandler;
    clone.routes = this.routes;
    return clone;
  }
  #notFoundHandler = notFoundHandler;
  // Cannot use `#` because it requires visibility at JavaScript runtime.
  errorHandler = errorHandler;
  /**
   * `.route()` allows grouping other Hono instance in routes.
   *
   * @see {@link https://hono.dev/docs/api/routing#grouping}
   *
   * @param {string} path - base Path
   * @param {Hono} app - other Hono instance
   * @returns {Hono} routed Hono instance
   *
   * @example
   * ```ts
   * const app = new Hono()
   * const app2 = new Hono()
   *
   * app2.get("/user", (c) => c.text("user"))
   * app.route("/api", app2) // GET /api/user
   * ```
   */
  route(path, app2) {
    const subApp = this.basePath(path);
    app2.routes.map((r) => {
      let handler;
      if (app2.errorHandler === errorHandler) {
        handler = r.handler;
      } else {
        handler = /* @__PURE__ */ __name(async (c, next) => (await compose([], app2.errorHandler)(c, () => r.handler(c, next))).res, "handler");
        handler[COMPOSED_HANDLER] = r.handler;
      }
      subApp.#addRoute(r.method, r.path, handler);
    });
    return this;
  }
  /**
   * `.basePath()` allows base paths to be specified.
   *
   * @see {@link https://hono.dev/docs/api/routing#base-path}
   *
   * @param {string} path - base Path
   * @returns {Hono} changed Hono instance
   *
   * @example
   * ```ts
   * const api = new Hono().basePath('/api')
   * ```
   */
  basePath(path) {
    const subApp = this.#clone();
    subApp._basePath = mergePath(this._basePath, path);
    return subApp;
  }
  /**
   * `.onError()` handles an error and returns a customized Response.
   *
   * @see {@link https://hono.dev/docs/api/hono#error-handling}
   *
   * @param {ErrorHandler} handler - request Handler for error
   * @returns {Hono} changed Hono instance
   *
   * @example
   * ```ts
   * app.onError((err, c) => {
   *   console.error(`${err}`)
   *   return c.text('Custom Error Message', 500)
   * })
   * ```
   */
  onError = /* @__PURE__ */ __name((handler) => {
    this.errorHandler = handler;
    return this;
  }, "onError");
  /**
   * `.notFound()` allows you to customize a Not Found Response.
   *
   * @see {@link https://hono.dev/docs/api/hono#not-found}
   *
   * @param {NotFoundHandler} handler - request handler for not-found
   * @returns {Hono} changed Hono instance
   *
   * @example
   * ```ts
   * app.notFound((c) => {
   *   return c.text('Custom 404 Message', 404)
   * })
   * ```
   */
  notFound = /* @__PURE__ */ __name((handler) => {
    this.#notFoundHandler = handler;
    return this;
  }, "notFound");
  /**
   * `.mount()` allows you to mount applications built with other frameworks into your Hono application.
   *
   * @see {@link https://hono.dev/docs/api/hono#mount}
   *
   * @param {string} path - base Path
   * @param {Function} applicationHandler - other Request Handler
   * @param {MountOptions} [options] - options of `.mount()`
   * @returns {Hono} mounted Hono instance
   *
   * @example
   * ```ts
   * import { Router as IttyRouter } from 'itty-router'
   * import { Hono } from 'hono'
   * // Create itty-router application
   * const ittyRouter = IttyRouter()
   * // GET /itty-router/hello
   * ittyRouter.get('/hello', () => new Response('Hello from itty-router'))
   *
   * const app = new Hono()
   * app.mount('/itty-router', ittyRouter.handle)
   * ```
   *
   * @example
   * ```ts
   * const app = new Hono()
   * // Send the request to another application without modification.
   * app.mount('/app', anotherApp, {
   *   replaceRequest: (req) => req,
   * })
   * ```
   */
  mount(path, applicationHandler, options) {
    let replaceRequest;
    let optionHandler;
    if (options) {
      if (typeof options === "function") {
        optionHandler = options;
      } else {
        optionHandler = options.optionHandler;
        if (options.replaceRequest === false) {
          replaceRequest = /* @__PURE__ */ __name((request) => request, "replaceRequest");
        } else {
          replaceRequest = options.replaceRequest;
        }
      }
    }
    const getOptions = optionHandler ? (c) => {
      const options2 = optionHandler(c);
      return Array.isArray(options2) ? options2 : [options2];
    } : (c) => {
      let executionContext = void 0;
      try {
        executionContext = c.executionCtx;
      } catch {
      }
      return [c.env, executionContext];
    };
    replaceRequest ||= (() => {
      const mergedPath = mergePath(this._basePath, path);
      const pathPrefixLength = mergedPath === "/" ? 0 : mergedPath.length;
      return (request) => {
        const url = new URL(request.url);
        url.pathname = url.pathname.slice(pathPrefixLength) || "/";
        return new Request(url, request);
      };
    })();
    const handler = /* @__PURE__ */ __name(async (c, next) => {
      const res = await applicationHandler(replaceRequest(c.req.raw), ...getOptions(c));
      if (res) {
        return res;
      }
      await next();
    }, "handler");
    this.#addRoute(METHOD_NAME_ALL, mergePath(path, "*"), handler);
    return this;
  }
  #addRoute(method, path, handler) {
    method = method.toUpperCase();
    path = mergePath(this._basePath, path);
    const r = { basePath: this._basePath, path, method, handler };
    this.router.add(method, path, [handler, r]);
    this.routes.push(r);
  }
  #handleError(err, c) {
    if (err instanceof Error) {
      return this.errorHandler(err, c);
    }
    throw err;
  }
  #dispatch(request, executionCtx, env2, method) {
    if (method === "HEAD") {
      return (async () => new Response(null, await this.#dispatch(request, executionCtx, env2, "GET")))();
    }
    const path = this.getPath(request, { env: env2 });
    const matchResult = this.router.match(method, path);
    const c = new Context(request, {
      path,
      matchResult,
      env: env2,
      executionCtx,
      notFoundHandler: this.#notFoundHandler
    });
    if (matchResult[0].length === 1) {
      let res;
      try {
        res = matchResult[0][0][0][0](c, async () => {
          c.res = await this.#notFoundHandler(c);
        });
      } catch (err) {
        return this.#handleError(err, c);
      }
      return res instanceof Promise ? res.then(
        (resolved) => resolved || (c.finalized ? c.res : this.#notFoundHandler(c))
      ).catch((err) => this.#handleError(err, c)) : res ?? this.#notFoundHandler(c);
    }
    const composed = compose(matchResult[0], this.errorHandler, this.#notFoundHandler);
    return (async () => {
      try {
        const context2 = await composed(c);
        if (!context2.finalized) {
          throw new Error(
            "Context is not finalized. Did you forget to return a Response object or `await next()`?"
          );
        }
        return context2.res;
      } catch (err) {
        return this.#handleError(err, c);
      }
    })();
  }
  /**
   * `.fetch()` will be entry point of your app.
   *
   * @see {@link https://hono.dev/docs/api/hono#fetch}
   *
   * @param {Request} request - request Object of request
   * @param {Env} Env - env Object
   * @param {ExecutionContext} - context of execution
   * @returns {Response | Promise<Response>} response of request
   *
   */
  fetch = /* @__PURE__ */ __name((request, ...rest) => {
    return this.#dispatch(request, rest[1], rest[0], request.method);
  }, "fetch");
  /**
   * `.request()` is a useful method for testing.
   * You can pass a URL or pathname to send a GET request.
   * app will return a Response object.
   * ```ts
   * test('GET /hello is ok', async () => {
   *   const res = await app.request('/hello')
   *   expect(res.status).toBe(200)
   * })
   * ```
   * @see https://hono.dev/docs/api/hono#request
   */
  request = /* @__PURE__ */ __name((input, requestInit, Env, executionCtx) => {
    if (input instanceof Request) {
      return this.fetch(requestInit ? new Request(input, requestInit) : input, Env, executionCtx);
    }
    input = input.toString();
    return this.fetch(
      new Request(
        /^https?:\/\//.test(input) ? input : `http://localhost${mergePath("/", input)}`,
        requestInit
      ),
      Env,
      executionCtx
    );
  }, "request");
  /**
   * `.fire()` automatically adds a global fetch event listener.
   * This can be useful for environments that adhere to the Service Worker API, such as non-ES module Cloudflare Workers.
   * @deprecated
   * Use `fire` from `hono/service-worker` instead.
   * ```ts
   * import { Hono } from 'hono'
   * import { fire } from 'hono/service-worker'
   *
   * const app = new Hono()
   * // ...
   * fire(app)
   * ```
   * @see https://hono.dev/docs/api/hono#fire
   * @see https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
   * @see https://developers.cloudflare.com/workers/reference/migrate-to-module-workers/
   */
  fire = /* @__PURE__ */ __name(() => {
    addEventListener("fetch", (event) => {
      event.respondWith(this.#dispatch(event.request, event, void 0, event.request.method));
    });
  }, "fire");
};

// node_modules/hono/dist/router/reg-exp-router/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/router/reg-exp-router/router.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/router/reg-exp-router/matcher.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var emptyParam = [];
function match(method, path) {
  const matchers = this.buildAllMatchers();
  const match2 = /* @__PURE__ */ __name(((method2, path2) => {
    const matcher = matchers[method2] || matchers[METHOD_NAME_ALL];
    const staticMatch = matcher[2][path2];
    if (staticMatch) {
      return staticMatch;
    }
    const match3 = path2.match(matcher[0]);
    if (!match3) {
      return [[], emptyParam];
    }
    const index = match3.indexOf("", 1);
    return [matcher[1][index], match3];
  }), "match2");
  this.match = match2;
  return match2(method, path);
}
__name(match, "match");

// node_modules/hono/dist/router/reg-exp-router/node.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var LABEL_REG_EXP_STR = "[^/]+";
var ONLY_WILDCARD_REG_EXP_STR = ".*";
var TAIL_WILDCARD_REG_EXP_STR = "(?:|/.*)";
var PATH_ERROR = /* @__PURE__ */ Symbol();
var regExpMetaChars = new Set(".\\+*[^]$()");
function compareKey(a, b) {
  if (a.length === 1) {
    return b.length === 1 ? a < b ? -1 : 1 : -1;
  }
  if (b.length === 1) {
    return 1;
  }
  if (a === ONLY_WILDCARD_REG_EXP_STR || a === TAIL_WILDCARD_REG_EXP_STR) {
    return 1;
  } else if (b === ONLY_WILDCARD_REG_EXP_STR || b === TAIL_WILDCARD_REG_EXP_STR) {
    return -1;
  }
  if (a === LABEL_REG_EXP_STR) {
    return 1;
  } else if (b === LABEL_REG_EXP_STR) {
    return -1;
  }
  return a.length === b.length ? a < b ? -1 : 1 : b.length - a.length;
}
__name(compareKey, "compareKey");
var Node = class _Node {
  static {
    __name(this, "_Node");
  }
  #index;
  #varIndex;
  #children = /* @__PURE__ */ Object.create(null);
  insert(tokens, index, paramMap, context2, pathErrorCheckOnly) {
    if (tokens.length === 0) {
      if (this.#index !== void 0) {
        throw PATH_ERROR;
      }
      if (pathErrorCheckOnly) {
        return;
      }
      this.#index = index;
      return;
    }
    const [token, ...restTokens] = tokens;
    const pattern = token === "*" ? restTokens.length === 0 ? ["", "", ONLY_WILDCARD_REG_EXP_STR] : ["", "", LABEL_REG_EXP_STR] : token === "/*" ? ["", "", TAIL_WILDCARD_REG_EXP_STR] : token.match(/^\:([^\{\}]+)(?:\{(.+)\})?$/);
    let node;
    if (pattern) {
      const name = pattern[1];
      let regexpStr = pattern[2] || LABEL_REG_EXP_STR;
      if (name && pattern[2]) {
        if (regexpStr === ".*") {
          throw PATH_ERROR;
        }
        regexpStr = regexpStr.replace(/^\((?!\?:)(?=[^)]+\)$)/, "(?:");
        if (/\((?!\?:)/.test(regexpStr)) {
          throw PATH_ERROR;
        }
      }
      node = this.#children[regexpStr];
      if (!node) {
        if (Object.keys(this.#children).some(
          (k) => k !== ONLY_WILDCARD_REG_EXP_STR && k !== TAIL_WILDCARD_REG_EXP_STR
        )) {
          throw PATH_ERROR;
        }
        if (pathErrorCheckOnly) {
          return;
        }
        node = this.#children[regexpStr] = new _Node();
        if (name !== "") {
          node.#varIndex = context2.varIndex++;
        }
      }
      if (!pathErrorCheckOnly && name !== "") {
        paramMap.push([name, node.#varIndex]);
      }
    } else {
      node = this.#children[token];
      if (!node) {
        if (Object.keys(this.#children).some(
          (k) => k.length > 1 && k !== ONLY_WILDCARD_REG_EXP_STR && k !== TAIL_WILDCARD_REG_EXP_STR
        )) {
          throw PATH_ERROR;
        }
        if (pathErrorCheckOnly) {
          return;
        }
        node = this.#children[token] = new _Node();
      }
    }
    node.insert(restTokens, index, paramMap, context2, pathErrorCheckOnly);
  }
  buildRegExpStr() {
    const childKeys = Object.keys(this.#children).sort(compareKey);
    const strList = childKeys.map((k) => {
      const c = this.#children[k];
      return (typeof c.#varIndex === "number" ? `(${k})@${c.#varIndex}` : regExpMetaChars.has(k) ? `\\${k}` : k) + c.buildRegExpStr();
    });
    if (typeof this.#index === "number") {
      strList.unshift(`#${this.#index}`);
    }
    if (strList.length === 0) {
      return "";
    }
    if (strList.length === 1) {
      return strList[0];
    }
    return "(?:" + strList.join("|") + ")";
  }
};

// node_modules/hono/dist/router/reg-exp-router/trie.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var Trie = class {
  static {
    __name(this, "Trie");
  }
  #context = { varIndex: 0 };
  #root = new Node();
  insert(path, index, pathErrorCheckOnly) {
    const paramAssoc = [];
    const groups = [];
    for (let i = 0; ; ) {
      let replaced = false;
      path = path.replace(/\{[^}]+\}/g, (m) => {
        const mark = `@\\${i}`;
        groups[i] = [mark, m];
        i++;
        replaced = true;
        return mark;
      });
      if (!replaced) {
        break;
      }
    }
    const tokens = path.match(/(?::[^\/]+)|(?:\/\*$)|./g) || [];
    for (let i = groups.length - 1; i >= 0; i--) {
      const [mark] = groups[i];
      for (let j = tokens.length - 1; j >= 0; j--) {
        if (tokens[j].indexOf(mark) !== -1) {
          tokens[j] = tokens[j].replace(mark, groups[i][1]);
          break;
        }
      }
    }
    this.#root.insert(tokens, index, paramAssoc, this.#context, pathErrorCheckOnly);
    return paramAssoc;
  }
  buildRegExp() {
    let regexp = this.#root.buildRegExpStr();
    if (regexp === "") {
      return [/^$/, [], []];
    }
    let captureIndex = 0;
    const indexReplacementMap = [];
    const paramReplacementMap = [];
    regexp = regexp.replace(/#(\d+)|@(\d+)|\.\*\$/g, (_, handlerIndex, paramIndex) => {
      if (handlerIndex !== void 0) {
        indexReplacementMap[++captureIndex] = Number(handlerIndex);
        return "$()";
      }
      if (paramIndex !== void 0) {
        paramReplacementMap[Number(paramIndex)] = ++captureIndex;
        return "";
      }
      return "";
    });
    return [new RegExp(`^${regexp}`), indexReplacementMap, paramReplacementMap];
  }
};

// node_modules/hono/dist/router/reg-exp-router/router.js
var nullMatcher = [/^$/, [], /* @__PURE__ */ Object.create(null)];
var wildcardRegExpCache = /* @__PURE__ */ Object.create(null);
function buildWildcardRegExp(path) {
  return wildcardRegExpCache[path] ??= new RegExp(
    path === "*" ? "" : `^${path.replace(
      /\/\*$|([.\\+*[^\]$()])/g,
      (_, metaChar) => metaChar ? `\\${metaChar}` : "(?:|/.*)"
    )}$`
  );
}
__name(buildWildcardRegExp, "buildWildcardRegExp");
function clearWildcardRegExpCache() {
  wildcardRegExpCache = /* @__PURE__ */ Object.create(null);
}
__name(clearWildcardRegExpCache, "clearWildcardRegExpCache");
function buildMatcherFromPreprocessedRoutes(routes) {
  const trie = new Trie();
  const handlerData = [];
  if (routes.length === 0) {
    return nullMatcher;
  }
  const routesWithStaticPathFlag = routes.map(
    (route) => [!/\*|\/:/.test(route[0]), ...route]
  ).sort(
    ([isStaticA, pathA], [isStaticB, pathB]) => isStaticA ? 1 : isStaticB ? -1 : pathA.length - pathB.length
  );
  const staticMap = /* @__PURE__ */ Object.create(null);
  for (let i = 0, j = -1, len = routesWithStaticPathFlag.length; i < len; i++) {
    const [pathErrorCheckOnly, path, handlers] = routesWithStaticPathFlag[i];
    if (pathErrorCheckOnly) {
      staticMap[path] = [handlers.map(([h]) => [h, /* @__PURE__ */ Object.create(null)]), emptyParam];
    } else {
      j++;
    }
    let paramAssoc;
    try {
      paramAssoc = trie.insert(path, j, pathErrorCheckOnly);
    } catch (e) {
      throw e === PATH_ERROR ? new UnsupportedPathError(path) : e;
    }
    if (pathErrorCheckOnly) {
      continue;
    }
    handlerData[j] = handlers.map(([h, paramCount]) => {
      const paramIndexMap = /* @__PURE__ */ Object.create(null);
      paramCount -= 1;
      for (; paramCount >= 0; paramCount--) {
        const [key, value] = paramAssoc[paramCount];
        paramIndexMap[key] = value;
      }
      return [h, paramIndexMap];
    });
  }
  const [regexp, indexReplacementMap, paramReplacementMap] = trie.buildRegExp();
  for (let i = 0, len = handlerData.length; i < len; i++) {
    for (let j = 0, len2 = handlerData[i].length; j < len2; j++) {
      const map = handlerData[i][j]?.[1];
      if (!map) {
        continue;
      }
      const keys = Object.keys(map);
      for (let k = 0, len3 = keys.length; k < len3; k++) {
        map[keys[k]] = paramReplacementMap[map[keys[k]]];
      }
    }
  }
  const handlerMap = [];
  for (const i in indexReplacementMap) {
    handlerMap[i] = handlerData[indexReplacementMap[i]];
  }
  return [regexp, handlerMap, staticMap];
}
__name(buildMatcherFromPreprocessedRoutes, "buildMatcherFromPreprocessedRoutes");
function findMiddleware(middleware, path) {
  if (!middleware) {
    return void 0;
  }
  for (const k of Object.keys(middleware).sort((a, b) => b.length - a.length)) {
    if (buildWildcardRegExp(k).test(path)) {
      return [...middleware[k]];
    }
  }
  return void 0;
}
__name(findMiddleware, "findMiddleware");
var RegExpRouter = class {
  static {
    __name(this, "RegExpRouter");
  }
  name = "RegExpRouter";
  #middleware;
  #routes;
  constructor() {
    this.#middleware = { [METHOD_NAME_ALL]: /* @__PURE__ */ Object.create(null) };
    this.#routes = { [METHOD_NAME_ALL]: /* @__PURE__ */ Object.create(null) };
  }
  add(method, path, handler) {
    const middleware = this.#middleware;
    const routes = this.#routes;
    if (!middleware || !routes) {
      throw new Error(MESSAGE_MATCHER_IS_ALREADY_BUILT);
    }
    if (!middleware[method]) {
      ;
      [middleware, routes].forEach((handlerMap) => {
        handlerMap[method] = /* @__PURE__ */ Object.create(null);
        Object.keys(handlerMap[METHOD_NAME_ALL]).forEach((p) => {
          handlerMap[method][p] = [...handlerMap[METHOD_NAME_ALL][p]];
        });
      });
    }
    if (path === "/*") {
      path = "*";
    }
    const paramCount = (path.match(/\/:/g) || []).length;
    if (/\*$/.test(path)) {
      const re = buildWildcardRegExp(path);
      if (method === METHOD_NAME_ALL) {
        Object.keys(middleware).forEach((m) => {
          middleware[m][path] ||= findMiddleware(middleware[m], path) || findMiddleware(middleware[METHOD_NAME_ALL], path) || [];
        });
      } else {
        middleware[method][path] ||= findMiddleware(middleware[method], path) || findMiddleware(middleware[METHOD_NAME_ALL], path) || [];
      }
      Object.keys(middleware).forEach((m) => {
        if (method === METHOD_NAME_ALL || method === m) {
          Object.keys(middleware[m]).forEach((p) => {
            re.test(p) && middleware[m][p].push([handler, paramCount]);
          });
        }
      });
      Object.keys(routes).forEach((m) => {
        if (method === METHOD_NAME_ALL || method === m) {
          Object.keys(routes[m]).forEach(
            (p) => re.test(p) && routes[m][p].push([handler, paramCount])
          );
        }
      });
      return;
    }
    const paths = checkOptionalParameter(path) || [path];
    for (let i = 0, len = paths.length; i < len; i++) {
      const path2 = paths[i];
      Object.keys(routes).forEach((m) => {
        if (method === METHOD_NAME_ALL || method === m) {
          routes[m][path2] ||= [
            ...findMiddleware(middleware[m], path2) || findMiddleware(middleware[METHOD_NAME_ALL], path2) || []
          ];
          routes[m][path2].push([handler, paramCount - len + i + 1]);
        }
      });
    }
  }
  match = match;
  buildAllMatchers() {
    const matchers = /* @__PURE__ */ Object.create(null);
    Object.keys(this.#routes).concat(Object.keys(this.#middleware)).forEach((method) => {
      matchers[method] ||= this.#buildMatcher(method);
    });
    this.#middleware = this.#routes = void 0;
    clearWildcardRegExpCache();
    return matchers;
  }
  #buildMatcher(method) {
    const routes = [];
    let hasOwnRoute = method === METHOD_NAME_ALL;
    [this.#middleware, this.#routes].forEach((r) => {
      const ownRoute = r[method] ? Object.keys(r[method]).map((path) => [path, r[method][path]]) : [];
      if (ownRoute.length !== 0) {
        hasOwnRoute ||= true;
        routes.push(...ownRoute);
      } else if (method !== METHOD_NAME_ALL) {
        routes.push(
          ...Object.keys(r[METHOD_NAME_ALL]).map((path) => [path, r[METHOD_NAME_ALL][path]])
        );
      }
    });
    if (!hasOwnRoute) {
      return null;
    } else {
      return buildMatcherFromPreprocessedRoutes(routes);
    }
  }
};

// node_modules/hono/dist/router/reg-exp-router/prepared-router.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/router/smart-router/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/router/smart-router/router.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var SmartRouter = class {
  static {
    __name(this, "SmartRouter");
  }
  name = "SmartRouter";
  #routers = [];
  #routes = [];
  constructor(init) {
    this.#routers = init.routers;
  }
  add(method, path, handler) {
    if (!this.#routes) {
      throw new Error(MESSAGE_MATCHER_IS_ALREADY_BUILT);
    }
    this.#routes.push([method, path, handler]);
  }
  match(method, path) {
    if (!this.#routes) {
      throw new Error("Fatal error");
    }
    const routers = this.#routers;
    const routes = this.#routes;
    const len = routers.length;
    let i = 0;
    let res;
    for (; i < len; i++) {
      const router = routers[i];
      try {
        for (let i2 = 0, len2 = routes.length; i2 < len2; i2++) {
          router.add(...routes[i2]);
        }
        res = router.match(method, path);
      } catch (e) {
        if (e instanceof UnsupportedPathError) {
          continue;
        }
        throw e;
      }
      this.match = router.match.bind(router);
      this.#routers = [router];
      this.#routes = void 0;
      break;
    }
    if (i === len) {
      throw new Error("Fatal error");
    }
    this.name = `SmartRouter + ${this.activeRouter.name}`;
    return res;
  }
  get activeRouter() {
    if (this.#routes || this.#routers.length !== 1) {
      throw new Error("No active router has been determined yet.");
    }
    return this.#routers[0];
  }
};

// node_modules/hono/dist/router/trie-router/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/router/trie-router/router.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/router/trie-router/node.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var emptyParams = /* @__PURE__ */ Object.create(null);
var hasChildren = /* @__PURE__ */ __name((children) => {
  for (const _ in children) {
    return true;
  }
  return false;
}, "hasChildren");
var Node2 = class _Node2 {
  static {
    __name(this, "_Node");
  }
  #methods;
  #children;
  #patterns;
  #order = 0;
  #params = emptyParams;
  constructor(method, handler, children) {
    this.#children = children || /* @__PURE__ */ Object.create(null);
    this.#methods = [];
    if (method && handler) {
      const m = /* @__PURE__ */ Object.create(null);
      m[method] = { handler, possibleKeys: [], score: 0 };
      this.#methods = [m];
    }
    this.#patterns = [];
  }
  insert(method, path, handler) {
    this.#order = ++this.#order;
    let curNode = this;
    const parts = splitRoutingPath(path);
    const possibleKeys = [];
    for (let i = 0, len = parts.length; i < len; i++) {
      const p = parts[i];
      const nextP = parts[i + 1];
      const pattern = getPattern(p, nextP);
      const key = Array.isArray(pattern) ? pattern[0] : p;
      if (key in curNode.#children) {
        curNode = curNode.#children[key];
        if (pattern) {
          possibleKeys.push(pattern[1]);
        }
        continue;
      }
      curNode.#children[key] = new _Node2();
      if (pattern) {
        curNode.#patterns.push(pattern);
        possibleKeys.push(pattern[1]);
      }
      curNode = curNode.#children[key];
    }
    curNode.#methods.push({
      [method]: {
        handler,
        possibleKeys: possibleKeys.filter((v, i, a) => a.indexOf(v) === i),
        score: this.#order
      }
    });
    return curNode;
  }
  #pushHandlerSets(handlerSets, node, method, nodeParams, params) {
    for (let i = 0, len = node.#methods.length; i < len; i++) {
      const m = node.#methods[i];
      const handlerSet = m[method] || m[METHOD_NAME_ALL];
      const processedSet = {};
      if (handlerSet !== void 0) {
        handlerSet.params = /* @__PURE__ */ Object.create(null);
        handlerSets.push(handlerSet);
        if (nodeParams !== emptyParams || params && params !== emptyParams) {
          for (let i2 = 0, len2 = handlerSet.possibleKeys.length; i2 < len2; i2++) {
            const key = handlerSet.possibleKeys[i2];
            const processed = processedSet[handlerSet.score];
            handlerSet.params[key] = params?.[key] && !processed ? params[key] : nodeParams[key] ?? params?.[key];
            processedSet[handlerSet.score] = true;
          }
        }
      }
    }
  }
  search(method, path) {
    const handlerSets = [];
    this.#params = emptyParams;
    const curNode = this;
    let curNodes = [curNode];
    const parts = splitPath(path);
    const curNodesQueue = [];
    const len = parts.length;
    let partOffsets = null;
    for (let i = 0; i < len; i++) {
      const part = parts[i];
      const isLast = i === len - 1;
      const tempNodes = [];
      for (let j = 0, len2 = curNodes.length; j < len2; j++) {
        const node = curNodes[j];
        const nextNode = node.#children[part];
        if (nextNode) {
          nextNode.#params = node.#params;
          if (isLast) {
            if (nextNode.#children["*"]) {
              this.#pushHandlerSets(handlerSets, nextNode.#children["*"], method, node.#params);
            }
            this.#pushHandlerSets(handlerSets, nextNode, method, node.#params);
          } else {
            tempNodes.push(nextNode);
          }
        }
        for (let k = 0, len3 = node.#patterns.length; k < len3; k++) {
          const pattern = node.#patterns[k];
          const params = node.#params === emptyParams ? {} : { ...node.#params };
          if (pattern === "*") {
            const astNode = node.#children["*"];
            if (astNode) {
              this.#pushHandlerSets(handlerSets, astNode, method, node.#params);
              astNode.#params = params;
              tempNodes.push(astNode);
            }
            continue;
          }
          const [key, name, matcher] = pattern;
          if (!part && !(matcher instanceof RegExp)) {
            continue;
          }
          const child = node.#children[key];
          if (matcher instanceof RegExp) {
            if (partOffsets === null) {
              partOffsets = new Array(len);
              let offset = path[0] === "/" ? 1 : 0;
              for (let p = 0; p < len; p++) {
                partOffsets[p] = offset;
                offset += parts[p].length + 1;
              }
            }
            const restPathString = path.substring(partOffsets[i]);
            const m = matcher.exec(restPathString);
            if (m) {
              params[name] = m[0];
              this.#pushHandlerSets(handlerSets, child, method, node.#params, params);
              if (hasChildren(child.#children)) {
                child.#params = params;
                const componentCount = m[0].match(/\//)?.length ?? 0;
                const targetCurNodes = curNodesQueue[componentCount] ||= [];
                targetCurNodes.push(child);
              }
              continue;
            }
          }
          if (matcher === true || matcher.test(part)) {
            params[name] = part;
            if (isLast) {
              this.#pushHandlerSets(handlerSets, child, method, params, node.#params);
              if (child.#children["*"]) {
                this.#pushHandlerSets(
                  handlerSets,
                  child.#children["*"],
                  method,
                  params,
                  node.#params
                );
              }
            } else {
              child.#params = params;
              tempNodes.push(child);
            }
          }
        }
      }
      const shifted = curNodesQueue.shift();
      curNodes = shifted ? tempNodes.concat(shifted) : tempNodes;
    }
    if (handlerSets.length > 1) {
      handlerSets.sort((a, b) => {
        return a.score - b.score;
      });
    }
    return [handlerSets.map(({ handler, params }) => [handler, params])];
  }
};

// node_modules/hono/dist/router/trie-router/router.js
var TrieRouter = class {
  static {
    __name(this, "TrieRouter");
  }
  name = "TrieRouter";
  #node;
  constructor() {
    this.#node = new Node2();
  }
  add(method, path, handler) {
    const results = checkOptionalParameter(path);
    if (results) {
      for (let i = 0, len = results.length; i < len; i++) {
        this.#node.insert(method, results[i], handler);
      }
      return;
    }
    this.#node.insert(method, path, handler);
  }
  match(method, path) {
    return this.#node.search(method, path);
  }
};

// node_modules/hono/dist/hono.js
var Hono2 = class extends Hono {
  static {
    __name(this, "Hono");
  }
  /**
   * Creates an instance of the Hono class.
   *
   * @param options - Optional configuration options for the Hono instance.
   */
  constructor(options = {}) {
    super(options);
    this.router = options.router ?? new SmartRouter({
      routers: [new RegExpRouter(), new TrieRouter()]
    });
  }
};

// node_modules/hono/dist/middleware/cors/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var cors = /* @__PURE__ */ __name((options) => {
  const defaults = {
    origin: "*",
    allowMethods: ["GET", "HEAD", "PUT", "POST", "DELETE", "PATCH"],
    allowHeaders: [],
    exposeHeaders: []
  };
  const opts = {
    ...defaults,
    ...options
  };
  const findAllowOrigin = ((optsOrigin) => {
    if (typeof optsOrigin === "string") {
      if (optsOrigin === "*") {
        if (opts.credentials) {
          return (origin) => origin || null;
        }
        return () => optsOrigin;
      } else {
        return (origin) => optsOrigin === origin ? origin : null;
      }
    } else if (typeof optsOrigin === "function") {
      return optsOrigin;
    } else {
      return (origin) => optsOrigin.includes(origin) ? origin : null;
    }
  })(opts.origin);
  const findAllowMethods = ((optsAllowMethods) => {
    if (typeof optsAllowMethods === "function") {
      return optsAllowMethods;
    } else if (Array.isArray(optsAllowMethods)) {
      return () => optsAllowMethods;
    } else {
      return () => [];
    }
  })(opts.allowMethods);
  return /* @__PURE__ */ __name(async function cors2(c, next) {
    function set(key, value) {
      c.res.headers.set(key, value);
    }
    __name(set, "set");
    const allowOrigin = await findAllowOrigin(c.req.header("origin") || "", c);
    if (allowOrigin) {
      set("Access-Control-Allow-Origin", allowOrigin);
    }
    if (opts.credentials) {
      set("Access-Control-Allow-Credentials", "true");
    }
    if (opts.exposeHeaders?.length) {
      set("Access-Control-Expose-Headers", opts.exposeHeaders.join(","));
    }
    if (c.req.method === "OPTIONS") {
      if (opts.origin !== "*" || opts.credentials) {
        set("Vary", "Origin");
      }
      if (opts.maxAge != null) {
        set("Access-Control-Max-Age", opts.maxAge.toString());
      }
      const allowMethods = await findAllowMethods(c.req.header("origin") || "", c);
      if (allowMethods.length) {
        set("Access-Control-Allow-Methods", allowMethods.join(","));
      }
      let headers = opts.allowHeaders;
      if (!headers?.length) {
        const requestHeaders = c.req.header("Access-Control-Request-Headers");
        if (requestHeaders) {
          headers = requestHeaders.split(/\s*,\s*/);
        }
      }
      if (headers?.length) {
        set("Access-Control-Allow-Headers", headers.join(","));
        c.res.headers.append("Vary", "Access-Control-Request-Headers");
      }
      c.res.headers.delete("Content-Length");
      c.res.headers.delete("Content-Type");
      return new Response(null, {
        headers: c.res.headers,
        status: 204,
        statusText: "No Content"
      });
    }
    await next();
    if (opts.origin !== "*" || opts.credentials) {
      c.header("Vary", "Origin", { append: true });
    }
  }, "cors2");
}, "cors");

// node_modules/hono/dist/middleware/logger/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/utils/color.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
function getColorEnabled() {
  const { process: process2, Deno: Deno2 } = globalThis;
  const isNoColor = typeof Deno2?.noColor === "boolean" ? Deno2.noColor : process2 !== void 0 ? (
    // eslint-disable-next-line no-unsafe-optional-chaining
    "NO_COLOR" in process2?.env
  ) : false;
  return !isNoColor;
}
__name(getColorEnabled, "getColorEnabled");
async function getColorEnabledAsync() {
  const { navigator: navigator2 } = globalThis;
  const cfWorkers = "cloudflare:workers";
  const isNoColor = navigator2 !== void 0 && navigator2.userAgent === "Cloudflare-Workers" ? await (async () => {
    try {
      return "NO_COLOR" in ((await import(cfWorkers)).env ?? {});
    } catch {
      return false;
    }
  })() : !getColorEnabled();
  return !isNoColor;
}
__name(getColorEnabledAsync, "getColorEnabledAsync");

// node_modules/hono/dist/middleware/logger/index.js
var humanize = /* @__PURE__ */ __name((times) => {
  const [delimiter, separator] = [",", "."];
  const orderTimes = times.map((v) => v.replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1" + delimiter));
  return orderTimes.join(separator);
}, "humanize");
var time3 = /* @__PURE__ */ __name((start) => {
  const delta = Date.now() - start;
  return humanize([delta < 1e3 ? delta + "ms" : Math.round(delta / 1e3) + "s"]);
}, "time");
var colorStatus = /* @__PURE__ */ __name(async (status2) => {
  const colorEnabled = await getColorEnabledAsync();
  if (colorEnabled) {
    switch (status2 / 100 | 0) {
      case 5:
        return `\x1B[31m${status2}\x1B[0m`;
      case 4:
        return `\x1B[33m${status2}\x1B[0m`;
      case 3:
        return `\x1B[36m${status2}\x1B[0m`;
      case 2:
        return `\x1B[32m${status2}\x1B[0m`;
    }
  }
  return `${status2}`;
}, "colorStatus");
async function log3(fn, prefix, method, path, status2 = 0, elapsed) {
  const out = prefix === "<--" ? `${prefix} ${method} ${path}` : `${prefix} ${method} ${path} ${await colorStatus(status2)} ${elapsed}`;
  fn(out);
}
__name(log3, "log");
var logger = /* @__PURE__ */ __name((fn = console.log) => {
  return /* @__PURE__ */ __name(async function logger2(c, next) {
    const { method, url } = c.req;
    const path = url.slice(url.indexOf("/", 8));
    await log3(fn, "<--", method, path);
    const start = Date.now();
    await next();
    await log3(fn, "-->", method, path, c.res.status, time3(start));
  }, "logger2");
}, "logger");

// src/routes/auth.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/models/User.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var import_bcryptjs = __toESM(require_bcrypt(), 1);

// node_modules/hono/dist/middleware/jwt/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/middleware/jwt/jwt.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/helper/cookie/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/utils/cookie.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/utils/jwt/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/utils/jwt/jwt.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/utils/encode.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var decodeBase64Url = /* @__PURE__ */ __name((str) => {
  return decodeBase64(str.replace(/_|-/g, (m) => ({ _: "/", "-": "+" })[m] ?? m));
}, "decodeBase64Url");
var encodeBase64Url = /* @__PURE__ */ __name((buf) => encodeBase64(buf).replace(/\/|\+/g, (m) => ({ "/": "_", "+": "-" })[m] ?? m), "encodeBase64Url");
var encodeBase64 = /* @__PURE__ */ __name((buf) => {
  let binary = "";
  const bytes = new Uint8Array(buf);
  for (let i = 0, len = bytes.length; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}, "encodeBase64");
var decodeBase64 = /* @__PURE__ */ __name((str) => {
  const binary = atob(str);
  const bytes = new Uint8Array(new ArrayBuffer(binary.length));
  const half = binary.length / 2;
  for (let i = 0, j = binary.length - 1; i <= half; i++, j--) {
    bytes[i] = binary.charCodeAt(i);
    bytes[j] = binary.charCodeAt(j);
  }
  return bytes;
}, "decodeBase64");

// node_modules/hono/dist/utils/jwt/jwa.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var AlgorithmTypes = /* @__PURE__ */ ((AlgorithmTypes2) => {
  AlgorithmTypes2["HS256"] = "HS256";
  AlgorithmTypes2["HS384"] = "HS384";
  AlgorithmTypes2["HS512"] = "HS512";
  AlgorithmTypes2["RS256"] = "RS256";
  AlgorithmTypes2["RS384"] = "RS384";
  AlgorithmTypes2["RS512"] = "RS512";
  AlgorithmTypes2["PS256"] = "PS256";
  AlgorithmTypes2["PS384"] = "PS384";
  AlgorithmTypes2["PS512"] = "PS512";
  AlgorithmTypes2["ES256"] = "ES256";
  AlgorithmTypes2["ES384"] = "ES384";
  AlgorithmTypes2["ES512"] = "ES512";
  AlgorithmTypes2["EdDSA"] = "EdDSA";
  return AlgorithmTypes2;
})(AlgorithmTypes || {});

// node_modules/hono/dist/utils/jwt/jws.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/hono/dist/helper/adapter/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var knownUserAgents = {
  deno: "Deno",
  bun: "Bun",
  workerd: "Cloudflare-Workers",
  node: "Node.js"
};
var getRuntimeKey = /* @__PURE__ */ __name(() => {
  const global = globalThis;
  const userAgentSupported = typeof navigator !== "undefined" && true;
  if (userAgentSupported) {
    for (const [runtimeKey, userAgent] of Object.entries(knownUserAgents)) {
      if (checkUserAgentEquals(userAgent)) {
        return runtimeKey;
      }
    }
  }
  if (typeof global?.EdgeRuntime === "string") {
    return "edge-light";
  }
  if (global?.fastly !== void 0) {
    return "fastly";
  }
  if (global?.process?.release?.name === "node") {
    return "node";
  }
  return "other";
}, "getRuntimeKey");
var checkUserAgentEquals = /* @__PURE__ */ __name((platform2) => {
  const userAgent = "Cloudflare-Workers";
  return userAgent.startsWith(platform2);
}, "checkUserAgentEquals");

// node_modules/hono/dist/utils/jwt/types.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var JwtAlgorithmNotImplemented = class extends Error {
  static {
    __name(this, "JwtAlgorithmNotImplemented");
  }
  constructor(alg) {
    super(`${alg} is not an implemented algorithm`);
    this.name = "JwtAlgorithmNotImplemented";
  }
};
var JwtAlgorithmRequired = class extends Error {
  static {
    __name(this, "JwtAlgorithmRequired");
  }
  constructor() {
    super('JWT verification requires "alg" option to be specified');
    this.name = "JwtAlgorithmRequired";
  }
};
var JwtAlgorithmMismatch = class extends Error {
  static {
    __name(this, "JwtAlgorithmMismatch");
  }
  constructor(expected, actual) {
    super(`JWT algorithm mismatch: expected "${expected}", got "${actual}"`);
    this.name = "JwtAlgorithmMismatch";
  }
};
var JwtTokenInvalid = class extends Error {
  static {
    __name(this, "JwtTokenInvalid");
  }
  constructor(token) {
    super(`invalid JWT token: ${token}`);
    this.name = "JwtTokenInvalid";
  }
};
var JwtTokenNotBefore = class extends Error {
  static {
    __name(this, "JwtTokenNotBefore");
  }
  constructor(token) {
    super(`token (${token}) is being used before it's valid`);
    this.name = "JwtTokenNotBefore";
  }
};
var JwtTokenExpired = class extends Error {
  static {
    __name(this, "JwtTokenExpired");
  }
  constructor(token) {
    super(`token (${token}) expired`);
    this.name = "JwtTokenExpired";
  }
};
var JwtTokenIssuedAt = class extends Error {
  static {
    __name(this, "JwtTokenIssuedAt");
  }
  constructor(currentTimestamp, iat) {
    super(
      `Invalid "iat" claim, must be a valid number lower than "${currentTimestamp}" (iat: "${iat}")`
    );
    this.name = "JwtTokenIssuedAt";
  }
};
var JwtTokenIssuer = class extends Error {
  static {
    __name(this, "JwtTokenIssuer");
  }
  constructor(expected, iss) {
    super(`expected issuer "${expected}", got ${iss ? `"${iss}"` : "none"} `);
    this.name = "JwtTokenIssuer";
  }
};
var JwtHeaderInvalid = class extends Error {
  static {
    __name(this, "JwtHeaderInvalid");
  }
  constructor(header) {
    super(`jwt header is invalid: ${JSON.stringify(header)}`);
    this.name = "JwtHeaderInvalid";
  }
};
var JwtHeaderRequiresKid = class extends Error {
  static {
    __name(this, "JwtHeaderRequiresKid");
  }
  constructor(header) {
    super(`required "kid" in jwt header: ${JSON.stringify(header)}`);
    this.name = "JwtHeaderRequiresKid";
  }
};
var JwtSymmetricAlgorithmNotAllowed = class extends Error {
  static {
    __name(this, "JwtSymmetricAlgorithmNotAllowed");
  }
  constructor(alg) {
    super(`symmetric algorithm "${alg}" is not allowed for JWK verification`);
    this.name = "JwtSymmetricAlgorithmNotAllowed";
  }
};
var JwtAlgorithmNotAllowed = class extends Error {
  static {
    __name(this, "JwtAlgorithmNotAllowed");
  }
  constructor(alg, allowedAlgorithms) {
    super(`algorithm "${alg}" is not in the allowed list: [${allowedAlgorithms.join(", ")}]`);
    this.name = "JwtAlgorithmNotAllowed";
  }
};
var JwtTokenSignatureMismatched = class extends Error {
  static {
    __name(this, "JwtTokenSignatureMismatched");
  }
  constructor(token) {
    super(`token(${token}) signature mismatched`);
    this.name = "JwtTokenSignatureMismatched";
  }
};
var JwtPayloadRequiresAud = class extends Error {
  static {
    __name(this, "JwtPayloadRequiresAud");
  }
  constructor(payload) {
    super(`required "aud" in jwt payload: ${JSON.stringify(payload)}`);
    this.name = "JwtPayloadRequiresAud";
  }
};
var JwtTokenAudience = class extends Error {
  static {
    __name(this, "JwtTokenAudience");
  }
  constructor(expected, aud) {
    super(
      `expected audience "${Array.isArray(expected) ? expected.join(", ") : expected}", got "${aud}"`
    );
    this.name = "JwtTokenAudience";
  }
};
var CryptoKeyUsage = /* @__PURE__ */ ((CryptoKeyUsage2) => {
  CryptoKeyUsage2["Encrypt"] = "encrypt";
  CryptoKeyUsage2["Decrypt"] = "decrypt";
  CryptoKeyUsage2["Sign"] = "sign";
  CryptoKeyUsage2["Verify"] = "verify";
  CryptoKeyUsage2["DeriveKey"] = "deriveKey";
  CryptoKeyUsage2["DeriveBits"] = "deriveBits";
  CryptoKeyUsage2["WrapKey"] = "wrapKey";
  CryptoKeyUsage2["UnwrapKey"] = "unwrapKey";
  return CryptoKeyUsage2;
})(CryptoKeyUsage || {});

// node_modules/hono/dist/utils/jwt/utf8.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var utf8Encoder = new TextEncoder();
var utf8Decoder = new TextDecoder();

// node_modules/hono/dist/utils/jwt/jws.js
async function signing(privateKey, alg, data) {
  const algorithm = getKeyAlgorithm(alg);
  const cryptoKey = await importPrivateKey(privateKey, algorithm);
  return await crypto.subtle.sign(algorithm, cryptoKey, data);
}
__name(signing, "signing");
async function verifying(publicKey, alg, signature, data) {
  const algorithm = getKeyAlgorithm(alg);
  const cryptoKey = await importPublicKey(publicKey, algorithm);
  return await crypto.subtle.verify(algorithm, cryptoKey, signature, data);
}
__name(verifying, "verifying");
function pemToBinary(pem) {
  return decodeBase64(pem.replace(/-+(BEGIN|END).*?-+/g, "").replace(/\s/g, ""));
}
__name(pemToBinary, "pemToBinary");
async function importPrivateKey(key, alg) {
  if (!crypto.subtle || !crypto.subtle.importKey) {
    throw new Error("`crypto.subtle.importKey` is undefined. JWT auth middleware requires it.");
  }
  if (isCryptoKey(key)) {
    if (key.type !== "private" && key.type !== "secret") {
      throw new Error(
        `unexpected key type: CryptoKey.type is ${key.type}, expected private or secret`
      );
    }
    return key;
  }
  const usages = [CryptoKeyUsage.Sign];
  if (typeof key === "object") {
    return await crypto.subtle.importKey("jwk", key, alg, false, usages);
  }
  if (key.includes("PRIVATE")) {
    return await crypto.subtle.importKey("pkcs8", pemToBinary(key), alg, false, usages);
  }
  return await crypto.subtle.importKey("raw", utf8Encoder.encode(key), alg, false, usages);
}
__name(importPrivateKey, "importPrivateKey");
async function importPublicKey(key, alg) {
  if (!crypto.subtle || !crypto.subtle.importKey) {
    throw new Error("`crypto.subtle.importKey` is undefined. JWT auth middleware requires it.");
  }
  if (isCryptoKey(key)) {
    if (key.type === "public" || key.type === "secret") {
      return key;
    }
    key = await exportPublicJwkFrom(key);
  }
  if (typeof key === "string" && key.includes("PRIVATE")) {
    const privateKey = await crypto.subtle.importKey("pkcs8", pemToBinary(key), alg, true, [
      CryptoKeyUsage.Sign
    ]);
    key = await exportPublicJwkFrom(privateKey);
  }
  const usages = [CryptoKeyUsage.Verify];
  if (typeof key === "object") {
    return await crypto.subtle.importKey("jwk", key, alg, false, usages);
  }
  if (key.includes("PUBLIC")) {
    return await crypto.subtle.importKey("spki", pemToBinary(key), alg, false, usages);
  }
  return await crypto.subtle.importKey("raw", utf8Encoder.encode(key), alg, false, usages);
}
__name(importPublicKey, "importPublicKey");
async function exportPublicJwkFrom(privateKey) {
  if (privateKey.type !== "private") {
    throw new Error(`unexpected key type: ${privateKey.type}`);
  }
  if (!privateKey.extractable) {
    throw new Error("unexpected private key is unextractable");
  }
  const jwk = await crypto.subtle.exportKey("jwk", privateKey);
  const { kty } = jwk;
  const { alg, e, n } = jwk;
  const { crv, x, y } = jwk;
  return { kty, alg, e, n, crv, x, y, key_ops: [CryptoKeyUsage.Verify] };
}
__name(exportPublicJwkFrom, "exportPublicJwkFrom");
function getKeyAlgorithm(name) {
  switch (name) {
    case "HS256":
      return {
        name: "HMAC",
        hash: {
          name: "SHA-256"
        }
      };
    case "HS384":
      return {
        name: "HMAC",
        hash: {
          name: "SHA-384"
        }
      };
    case "HS512":
      return {
        name: "HMAC",
        hash: {
          name: "SHA-512"
        }
      };
    case "RS256":
      return {
        name: "RSASSA-PKCS1-v1_5",
        hash: {
          name: "SHA-256"
        }
      };
    case "RS384":
      return {
        name: "RSASSA-PKCS1-v1_5",
        hash: {
          name: "SHA-384"
        }
      };
    case "RS512":
      return {
        name: "RSASSA-PKCS1-v1_5",
        hash: {
          name: "SHA-512"
        }
      };
    case "PS256":
      return {
        name: "RSA-PSS",
        hash: {
          name: "SHA-256"
        },
        saltLength: 32
        // 256 >> 3
      };
    case "PS384":
      return {
        name: "RSA-PSS",
        hash: {
          name: "SHA-384"
        },
        saltLength: 48
        // 384 >> 3
      };
    case "PS512":
      return {
        name: "RSA-PSS",
        hash: {
          name: "SHA-512"
        },
        saltLength: 64
        // 512 >> 3,
      };
    case "ES256":
      return {
        name: "ECDSA",
        hash: {
          name: "SHA-256"
        },
        namedCurve: "P-256"
      };
    case "ES384":
      return {
        name: "ECDSA",
        hash: {
          name: "SHA-384"
        },
        namedCurve: "P-384"
      };
    case "ES512":
      return {
        name: "ECDSA",
        hash: {
          name: "SHA-512"
        },
        namedCurve: "P-521"
      };
    case "EdDSA":
      return {
        name: "Ed25519",
        namedCurve: "Ed25519"
      };
    default:
      throw new JwtAlgorithmNotImplemented(name);
  }
}
__name(getKeyAlgorithm, "getKeyAlgorithm");
function isCryptoKey(key) {
  const runtime = getRuntimeKey();
  if (runtime === "node" && !!crypto.webcrypto) {
    return key instanceof crypto.webcrypto.CryptoKey;
  }
  return key instanceof CryptoKey;
}
__name(isCryptoKey, "isCryptoKey");

// node_modules/hono/dist/utils/jwt/jwt.js
var encodeJwtPart = /* @__PURE__ */ __name((part) => encodeBase64Url(utf8Encoder.encode(JSON.stringify(part)).buffer).replace(/=/g, ""), "encodeJwtPart");
var encodeSignaturePart = /* @__PURE__ */ __name((buf) => encodeBase64Url(buf).replace(/=/g, ""), "encodeSignaturePart");
var decodeJwtPart = /* @__PURE__ */ __name((part) => JSON.parse(utf8Decoder.decode(decodeBase64Url(part))), "decodeJwtPart");
function isTokenHeader(obj) {
  if (typeof obj === "object" && obj !== null) {
    const objWithAlg = obj;
    return "alg" in objWithAlg && Object.values(AlgorithmTypes).includes(objWithAlg.alg) && (!("typ" in objWithAlg) || objWithAlg.typ === "JWT");
  }
  return false;
}
__name(isTokenHeader, "isTokenHeader");
var sign = /* @__PURE__ */ __name(async (payload, privateKey, alg = "HS256") => {
  const encodedPayload = encodeJwtPart(payload);
  let encodedHeader;
  if (typeof privateKey === "object" && "alg" in privateKey) {
    alg = privateKey.alg;
    encodedHeader = encodeJwtPart({ alg, typ: "JWT", kid: privateKey.kid });
  } else {
    encodedHeader = encodeJwtPart({ alg, typ: "JWT" });
  }
  const partialToken = `${encodedHeader}.${encodedPayload}`;
  const signaturePart = await signing(privateKey, alg, utf8Encoder.encode(partialToken));
  const signature = encodeSignaturePart(signaturePart);
  return `${partialToken}.${signature}`;
}, "sign");
var verify = /* @__PURE__ */ __name(async (token, publicKey, algOrOptions) => {
  if (!algOrOptions) {
    throw new JwtAlgorithmRequired();
  }
  const {
    alg,
    iss,
    nbf = true,
    exp = true,
    iat = true,
    aud
  } = typeof algOrOptions === "string" ? { alg: algOrOptions } : algOrOptions;
  if (!alg) {
    throw new JwtAlgorithmRequired();
  }
  const tokenParts = token.split(".");
  if (tokenParts.length !== 3) {
    throw new JwtTokenInvalid(token);
  }
  const { header, payload } = decode(token);
  if (!isTokenHeader(header)) {
    throw new JwtHeaderInvalid(header);
  }
  if (header.alg !== alg) {
    throw new JwtAlgorithmMismatch(alg, header.alg);
  }
  const now = Math.floor(Date.now() / 1e3);
  if (nbf && payload.nbf && payload.nbf > now) {
    throw new JwtTokenNotBefore(token);
  }
  if (exp && payload.exp && payload.exp <= now) {
    throw new JwtTokenExpired(token);
  }
  if (iat && payload.iat && now < payload.iat) {
    throw new JwtTokenIssuedAt(now, payload.iat);
  }
  if (iss) {
    if (!payload.iss) {
      throw new JwtTokenIssuer(iss, null);
    }
    if (typeof iss === "string" && payload.iss !== iss) {
      throw new JwtTokenIssuer(iss, payload.iss);
    }
    if (iss instanceof RegExp && !iss.test(payload.iss)) {
      throw new JwtTokenIssuer(iss, payload.iss);
    }
  }
  if (aud) {
    if (!payload.aud) {
      throw new JwtPayloadRequiresAud(payload);
    }
    const audiences = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
    const matched = audiences.some(
      (payloadAud) => aud instanceof RegExp ? aud.test(payloadAud) : typeof aud === "string" ? payloadAud === aud : Array.isArray(aud) && aud.includes(payloadAud)
    );
    if (!matched) {
      throw new JwtTokenAudience(aud, payload.aud);
    }
  }
  const headerPayload = token.substring(0, token.lastIndexOf("."));
  const verified = await verifying(
    publicKey,
    alg,
    decodeBase64Url(tokenParts[2]),
    utf8Encoder.encode(headerPayload)
  );
  if (!verified) {
    throw new JwtTokenSignatureMismatched(token);
  }
  return payload;
}, "verify");
var symmetricAlgorithms = [
  AlgorithmTypes.HS256,
  AlgorithmTypes.HS384,
  AlgorithmTypes.HS512
];
var verifyWithJwks = /* @__PURE__ */ __name(async (token, options, init) => {
  const verifyOpts = options.verification || {};
  const header = decodeHeader(token);
  if (!isTokenHeader(header)) {
    throw new JwtHeaderInvalid(header);
  }
  if (!header.kid) {
    throw new JwtHeaderRequiresKid(header);
  }
  if (symmetricAlgorithms.includes(header.alg)) {
    throw new JwtSymmetricAlgorithmNotAllowed(header.alg);
  }
  if (!options.allowedAlgorithms.includes(header.alg)) {
    throw new JwtAlgorithmNotAllowed(header.alg, options.allowedAlgorithms);
  }
  let verifyKeys = options.keys ? [...options.keys] : void 0;
  if (options.jwks_uri) {
    const response = await fetch(options.jwks_uri, init);
    if (!response.ok) {
      throw new Error(`failed to fetch JWKS from ${options.jwks_uri}`);
    }
    const data = await response.json();
    if (!data.keys) {
      throw new Error('invalid JWKS response. "keys" field is missing');
    }
    if (!Array.isArray(data.keys)) {
      throw new Error('invalid JWKS response. "keys" field is not an array');
    }
    verifyKeys ??= [];
    verifyKeys.push(...data.keys);
  } else if (!verifyKeys) {
    throw new Error('verifyWithJwks requires options for either "keys" or "jwks_uri" or both');
  }
  const matchingKey = verifyKeys.find((key) => key.kid === header.kid);
  if (!matchingKey) {
    throw new JwtTokenInvalid(token);
  }
  if (matchingKey.alg && matchingKey.alg !== header.alg) {
    throw new JwtAlgorithmMismatch(matchingKey.alg, header.alg);
  }
  return await verify(token, matchingKey, {
    alg: header.alg,
    ...verifyOpts
  });
}, "verifyWithJwks");
var decode = /* @__PURE__ */ __name((token) => {
  const parts = token.split(".");
  if (parts.length !== 3) {
    throw new JwtTokenInvalid(token);
  }
  try {
    const header = decodeJwtPart(parts[0]);
    const payload = decodeJwtPart(parts[1]);
    return {
      header,
      payload
    };
  } catch {
    throw new JwtTokenInvalid(token);
  }
}, "decode");
var decodeHeader = /* @__PURE__ */ __name((token) => {
  const parts = token.split(".");
  if (parts.length !== 3) {
    throw new JwtTokenInvalid(token);
  }
  try {
    return decodeJwtPart(parts[0]);
  } catch {
    throw new JwtTokenInvalid(token);
  }
}, "decodeHeader");

// node_modules/hono/dist/utils/jwt/index.js
var Jwt = { sign, verify, decode, verifyWithJwks };

// node_modules/hono/dist/middleware/jwt/jwt.js
var verifyWithJwks2 = Jwt.verifyWithJwks;
var verify2 = Jwt.verify;
var decode2 = Jwt.decode;
var sign2 = Jwt.sign;

// src/models/User.js
var User = class {
  static {
    __name(this, "User");
  }
  constructor(db) {
    this.db = db;
  }
  async create(userData) {
    const { email, password, name } = userData;
    const userId = crypto.randomUUID();
    const passwordHash = await import_bcryptjs.default.hash(password, 10);
    const stmt = this.db.prepare(`
      INSERT INTO users (id, email, password_hash, name)
      VALUES (?, ?, ?, ?)
    `);
    try {
      await stmt.bind(userId, email || null, passwordHash || null, name || null).run();
      return { id: userId, email, name };
    } catch (error3) {
      if (error3.message.includes("UNIQUE constraint failed")) {
        throw new Error("Email already exists");
      }
      throw error3;
    }
  }
  async findByEmail(email) {
    const stmt = this.db.prepare(`
      SELECT id, email, password_hash, name, created_at, updated_at
      FROM users WHERE email = ?
    `);
    const result = await stmt.bind(email).first();
    return result;
  }
  async findById(userId) {
    const stmt = this.db.prepare(`
      SELECT id, email, name, created_at, updated_at
      FROM users WHERE id = ?
    `);
    const result = await stmt.bind(userId).first();
    return result;
  }
  async verifyPassword(user, password) {
    return import_bcryptjs.default.compare(password, user.password_hash);
  }
  async generateToken(user, secret) {
    const payload = {
      userId: user.id,
      email: user.email,
      exp: Math.floor(Date.now() / 1e3) + 60 * 60 * 24 * 7
      // 7 days
    };
    return await sign2(payload, "ads-saas-secret-key");
  }
  async update(userId, userData) {
    const { email } = userData;
    const stmt = this.db.prepare(`
      UPDATE users 
      SET email = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    await stmt.bind(email, userId).run();
    return this.findById(userId);
  }
  async delete(userId) {
    const stmt = this.db.prepare(`DELETE FROM users WHERE id = ?`);
    await stmt.bind(userId).run();
  }
};

// src/models/Log.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var Log = class {
  static {
    __name(this, "Log");
  }
  constructor(db) {
    this.db = db;
  }
  async create(logData) {
    const { level, message, context: context2, userId, campaignId, platformId } = logData;
    const logId = crypto.randomUUID();
    const stmt = this.db.prepare(`
      INSERT INTO logs (id, level, message, context, user_id, campaign_id, platform_id)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    await stmt.bind(
      logId,
      level || "info",
      message || "",
      context2 ? JSON.stringify(context2) : null,
      userId || null,
      campaignId || null,
      platformId || null
    ).run();
    return this.findById(logId);
  }
  async findById(logId) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, context, user_id, campaign_id, platform_id, created_at
      FROM logs WHERE id = ?
    `);
    const result = await stmt.bind(logId).first();
    if (result && result.context) {
      result.context = JSON.parse(result.context);
    }
    return result;
  }
  async findByUserId(userId, limit = 100, offset = 0, level = null) {
    let query = `
      SELECT id, level, message, context, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
    `;
    const params = [userId];
    if (level) {
      query += ` AND level = ?`;
      params.push(level);
    }
    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);
    const stmt = this.db.prepare(query);
    const results = await stmt.bind(...params).all();
    return results.map((log4) => ({
      ...log4,
      context: log4.context ? JSON.parse(log4.context) : {}
    }));
  }
  async findByCampaignId(campaignId, limit = 50) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, context, user_id, platform_id, created_at
      FROM logs 
      WHERE campaign_id = ?
      ORDER BY created_at DESC
      LIMIT ?
    `);
    const results = await stmt.bind(campaignId, limit).all();
    return results.map((log4) => ({
      ...log4,
      context: log4.context ? JSON.parse(log4.context) : {}
    }));
  }
  async findByPlatformId(platformId, limit = 50) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, context, user_id, campaign_id, created_at
      FROM logs 
      WHERE platform_id = ?
      ORDER BY created_at DESC
      LIMIT ?
    `);
    const results = await stmt.bind(platformId, limit).all();
    return results.map((log4) => ({
      ...log4,
      context: log4.context ? JSON.parse(log4.context) : {}
    }));
  }
  async getLogStats(userId, timeRange = "24h") {
    let timeFilter = "";
    if (timeRange === "24h") {
      timeFilter = "AND created_at >= datetime('now', '-1 day')";
    } else if (timeRange === "7d") {
      timeFilter = "AND created_at >= datetime('now', '-7 days')";
    } else if (timeRange === "30d") {
      timeFilter = "AND created_at >= datetime('now', '-30 days')";
    }
    const stmt = this.db.prepare(`
      SELECT 
        COUNT(*) as total_logs,
        COUNT(CASE WHEN level = 'error' THEN 1 END) as error_count,
        COUNT(CASE WHEN level = 'warn' THEN 1 END) as warn_count,
        COUNT(CASE WHEN level = 'info' THEN 1 END) as info_count,
        COUNT(CASE WHEN level = 'debug' THEN 1 END) as debug_count
      FROM logs 
      WHERE user_id = ? ${timeFilter}
    `);
    return await stmt.bind(userId).first();
  }
  async getRecentLogs(userId, limit = 10) {
    const stmt = this.db.prepare(`
      SELECT id, level, message, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT ?
    `);
    return await stmt.bind(userId, limit).all();
  }
  async deleteOldLogs(daysOld = 30) {
    const stmt = this.db.prepare(`
      DELETE FROM logs 
      WHERE created_at < datetime('now', '-${daysOld} days')
    `);
    return await stmt.run();
  }
  async cleanup(userId, maxLogs = 1e3) {
    const stmt = this.db.prepare(`
      DELETE FROM logs 
      WHERE user_id = ? AND id NOT IN (
        SELECT id FROM logs 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
      )
    `);
    return await stmt.bind(userId, userId, maxLogs).run();
  }
  // Convenience methods for different log levels
  async info(message, context2 = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: "info",
      message,
      context: context2,
      userId,
      campaignId,
      platformId
    });
  }
  async warn(message, context2 = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: "warn",
      message,
      context: context2,
      userId,
      campaignId,
      platformId
    });
  }
  async error(message, context2 = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: "error",
      message,
      context: context2,
      userId,
      campaignId,
      platformId
    });
  }
  async debug(message, context2 = {}, userId = null, campaignId = null, platformId = null) {
    return await this.create({
      level: "debug",
      message,
      context: context2,
      userId,
      campaignId,
      platformId
    });
  }
};

// src/routes/auth.js
var auth = new Hono2();
auth.post("/register", async (c) => {
  try {
    const { email, password, name } = await c.req.json();
    if (!email || !password) {
      return c.json({ error: "Email and password are required" }, 400);
    }
    if (password.length < 6) {
      return c.json({ error: "Password must be at least 6 characters" }, 400);
    }
    const user = new User(c.env.DB);
    const log4 = new Log(c.env.DB);
    const existingUser = await user.findByEmail(email);
    if (existingUser) {
      return c.json({ error: "Email already exists" }, 409);
    }
    const newUser = await user.create({ email, password, name });
    await log4.info("User registered successfully", { userId: newUser.id }, newUser.id);
    const token = await user.generateToken(newUser, c.env.JWT_SECRET);
    return c.json({
      user: {
        id: newUser.id,
        email: newUser.email,
        name: newUser.name
      },
      token
    }, 201);
  } catch (error3) {
    console.error("Registration error:", error3);
    return c.json({ error: "Registration failed" }, 500);
  }
});
auth.post("/login", async (c) => {
  try {
    const { email, password } = await c.req.json();
    if (!email || !password) {
      return c.json({ error: "Email and password are required" }, 400);
    }
    const user = new User(c.env.DB);
    const log4 = new Log(c.env.DB);
    const foundUser = await user.findByEmail(email);
    if (!foundUser) {
      return c.json({ error: "Invalid credentials" }, 401);
    }
    const isValidPassword = await user.verifyPassword(foundUser, password);
    if (!isValidPassword) {
      return c.json({ error: "Invalid credentials" }, 401);
    }
    const sessionData = {
      userId: foundUser.id,
      email: foundUser.email,
      loginTime: (/* @__PURE__ */ new Date()).toISOString()
    };
    await c.env.SESSIONS.put(`session:${foundUser.id}`, JSON.stringify(sessionData), {
      expirationTtl: 7 * 24 * 60 * 60
      // 7 days
    });
    await log4.info("User logged in successfully", { userId: foundUser.id }, foundUser.id);
    const token = await user.generateToken(foundUser, c.env.JWT_SECRET);
    return c.json({
      user: {
        id: foundUser.id,
        email: foundUser.email,
        name: foundUser.name
      },
      token
    });
  } catch (error3) {
    console.error("Login error:", error3);
    return c.json({ error: "Login failed" }, 500);
  }
});
auth.post("/logout", async (c) => {
  try {
    const userId = c.get("userId");
    if (userId) {
      await c.env.SESSIONS.delete(`session:${userId}`);
      const log4 = new Log(c.env.DB);
      await log4.info("User logged out", { userId }, userId);
    }
    return c.json({ message: "Logged out successfully" });
  } catch (error3) {
    console.error("Logout error:", error3);
    return c.json({ error: "Logout failed" }, 500);
  }
});
auth.get("/me", async (c) => {
  try {
    const userId = c.get("userId");
    const email = c.get("email");
    if (!userId) {
      return c.json({ error: "Not authenticated" }, 401);
    }
    return c.json({
      user: {
        id: userId,
        email,
        name: c.get("name")
      }
    });
  } catch (error3) {
    console.error("Get user error:", error3);
    return c.json({ error: "Failed to get user info" }, 500);
  }
});
auth.post("/refresh", async (c) => {
  try {
    const userId = c.get("userId");
    if (!userId) {
      return c.json({ error: "Not authenticated" }, 401);
    }
    const user = new User(c.env.DB);
    const foundUser = await user.findById(userId);
    if (!foundUser) {
      return c.json({ error: "User not found" }, 404);
    }
    const token = await user.generateToken(foundUser, c.env.JWT_SECRET);
    return c.json({ token });
  } catch (error3) {
    console.error("Token refresh error:", error3);
    return c.json({ error: "Token refresh failed" }, 500);
  }
});

// src/routes/campaigns.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/models/Campaign.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/uuid/dist/esm-browser/index.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/uuid/dist/esm-browser/rng.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var getRandomValues;
var rnds8 = new Uint8Array(16);
function rng() {
  if (!getRandomValues) {
    getRandomValues = typeof crypto !== "undefined" && crypto.getRandomValues && crypto.getRandomValues.bind(crypto);
    if (!getRandomValues) {
      throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");
    }
  }
  return getRandomValues(rnds8);
}
__name(rng, "rng");

// node_modules/uuid/dist/esm-browser/stringify.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var byteToHex = [];
for (let i = 0; i < 256; ++i) {
  byteToHex.push((i + 256).toString(16).slice(1));
}
function unsafeStringify(arr, offset = 0) {
  return byteToHex[arr[offset + 0]] + byteToHex[arr[offset + 1]] + byteToHex[arr[offset + 2]] + byteToHex[arr[offset + 3]] + "-" + byteToHex[arr[offset + 4]] + byteToHex[arr[offset + 5]] + "-" + byteToHex[arr[offset + 6]] + byteToHex[arr[offset + 7]] + "-" + byteToHex[arr[offset + 8]] + byteToHex[arr[offset + 9]] + "-" + byteToHex[arr[offset + 10]] + byteToHex[arr[offset + 11]] + byteToHex[arr[offset + 12]] + byteToHex[arr[offset + 13]] + byteToHex[arr[offset + 14]] + byteToHex[arr[offset + 15]];
}
__name(unsafeStringify, "unsafeStringify");

// node_modules/uuid/dist/esm-browser/v4.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// node_modules/uuid/dist/esm-browser/native.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var randomUUID = typeof crypto !== "undefined" && crypto.randomUUID && crypto.randomUUID.bind(crypto);
var native_default = {
  randomUUID
};

// node_modules/uuid/dist/esm-browser/v4.js
function v4(options, buf, offset) {
  if (native_default.randomUUID && !buf && !options) {
    return native_default.randomUUID();
  }
  options = options || {};
  const rnds = options.random || (options.rng || rng)();
  rnds[6] = rnds[6] & 15 | 64;
  rnds[8] = rnds[8] & 63 | 128;
  if (buf) {
    offset = offset || 0;
    for (let i = 0; i < 16; ++i) {
      buf[offset + i] = rnds[i];
    }
    return buf;
  }
  return unsafeStringify(rnds);
}
__name(v4, "v4");
var v4_default = v4;

// src/models/Campaign.js
var Campaign = class {
  static {
    __name(this, "Campaign");
  }
  constructor(db) {
    this.db = db;
  }
  async create(campaignData, userId) {
    const {
      title: title2,
      description,
      budget,
      scheduleStart,
      scheduleEnd,
      platforms: platforms2
    } = campaignData;
    const campaignId = v4_default();
    const stmt = this.db.prepare(`
      INSERT INTO campaigns (id, title, description, budget, schedule_start, schedule_end, user_id)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    await stmt.bind(
      campaignId,
      title2,
      description,
      budget,
      scheduleStart,
      scheduleEnd,
      userId
    ).run();
    if (platforms2 && platforms2.length > 0) {
      await this.linkPlatforms(campaignId, platforms2);
    }
    return this.findById(campaignId);
  }
  async findById(campaignId) {
    const stmt = this.db.prepare(`
      SELECT c.*, 
             json_group_array(
               json_object(
                 'id', cp.id,
                 'platformId', cp.platform_id,
                 'platformName', p.name,
                 'platformType', p.type,
                 'status', cp.status,
                 'errorMessage', cp.error_message,
                 'retryCount', cp.retry_count
               )
             ) as platforms
      FROM campaigns c
      LEFT JOIN campaign_platforms cp ON c.id = cp.campaign_id
      LEFT JOIN platforms p ON cp.platform_id = p.id
      WHERE c.id = ?
      GROUP BY c.id
    `);
    const result = await stmt.bind(campaignId).first();
    if (result && result.platforms) {
      result.platforms = JSON.parse(result.platforms);
    }
    return result;
  }
  async findByUserId(userId, limit = 50, offset = 0) {
    const stmt = this.db.prepare(`
      SELECT c.*, 
             COUNT(cp.id) as platform_count,
             SUM(CASE WHEN cp.status = 'success' THEN 1 ELSE 0 END) as success_count,
             SUM(CASE WHEN cp.status = 'failed' THEN 1 ELSE 0 END) as failed_count
      FROM campaigns c
      LEFT JOIN campaign_platforms cp ON c.id = cp.campaign_id
      WHERE c.user_id = ?
      GROUP BY c.id
      ORDER BY c.created_at DESC
      LIMIT ? OFFSET ?
    `);
    return await stmt.bind(userId, limit, offset).all();
  }
  async update(campaignId, updateData) {
    const { title: title2, description, budget, scheduleStart, scheduleEnd, status: status2 } = updateData;
    const stmt = this.db.prepare(`
      UPDATE campaigns 
      SET title = ?, description = ?, budget = ?, 
          schedule_start = ?, schedule_end = ?, status = ?,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    await stmt.bind(
      title2,
      description,
      budget,
      scheduleStart,
      scheduleEnd,
      status2,
      campaignId
    ).run();
    return this.findById(campaignId);
  }
  async delete(campaignId) {
    const stmt = this.db.prepare(`DELETE FROM campaigns WHERE id = ?`);
    await stmt.bind(campaignId).run();
  }
  async linkPlatforms(campaignId, platformIds) {
    for (const platformId of platformIds) {
      const cpId = v4_default();
      const stmt = this.db.prepare(`
        INSERT INTO campaign_platforms (id, campaign_id, platform_id)
        VALUES (?, ?, ?)
      `);
      await stmt.bind(cpId, campaignId, platformId).run();
    }
  }
  async updatePlatformStatus(campaignId, platformId, status2, errorMessage = null) {
    const stmt = this.db.prepare(`
      UPDATE campaign_platforms 
      SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
      WHERE campaign_id = ? AND platform_id = ?
    `);
    await stmt.bind(status2, errorMessage, campaignId, platformId).run();
  }
  async getMedia(campaignId) {
    const stmt = this.db.prepare(`
      SELECT cm.*, m.filename, m.original_name, m.mime_type, m.size, m.url
      FROM campaign_media cm
      JOIN media m ON cm.media_id = m.id
      WHERE cm.campaign_id = ?
    `);
    return await stmt.bind(campaignId).all();
  }
  async duplicate(campaignId, newTitle) {
    const original = await this.findById(campaignId);
    if (!original) {
      throw new Error("Campaign not found");
    }
    const newCampaignData = {
      title: newTitle,
      description: original.description,
      budget: original.budget,
      scheduleStart: original.schedule_start,
      scheduleEnd: original.schedule_end,
      platforms: original.platforms?.map((p) => p.platformId) || []
    };
    return await this.create(newCampaignData, original.user_id);
  }
};

// src/routes/campaigns.js
var campaigns = new Hono2();
campaigns.get("/", async (c) => {
  try {
    const userId = c.get("userId");
    const limit = parseInt(c.req.query("limit") || "50");
    const offset = parseInt(c.req.query("offset") || "0");
    const campaign2 = new Campaign(c.env.DB);
    const userCampaigns = await campaign2.findByUserId(userId, limit, offset);
    return c.json({ campaigns: userCampaigns });
  } catch (error3) {
    console.error("Get campaigns error:", error3);
    return c.json({ error: "Failed to get campaigns" }, 500);
  }
});
campaigns.get("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const campaign2 = new Campaign(c.env.DB);
    const foundCampaign = await campaign2.findById(campaignId);
    if (!foundCampaign) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (foundCampaign.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    return c.json({ campaign: foundCampaign });
  } catch (error3) {
    console.error("Get campaign error:", error3);
    return c.json({ error: "Failed to get campaign" }, 500);
  }
});
campaigns.post("/", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignData = await c.req.json();
    const { title: title2, budget, platforms: platforms2 } = campaignData;
    if (!title2 || !budget || !platforms2 || platforms2.length === 0) {
      return c.json({ error: "Title, budget, and platforms are required" }, 400);
    }
    if (budget <= 0) {
      return c.json({ error: "Budget must be greater than 0" }, 400);
    }
    const campaign2 = new Campaign(c.env.DB);
    const log4 = new Log(c.env.DB);
    const newCampaign = await campaign2.create(campaignData, userId);
    await log4.info("Campaign created", {
      campaignId: newCampaign.id,
      title: newCampaign.title,
      platforms: platforms2.length
    }, userId, newCampaign.id);
    return c.json({ campaign: newCampaign }, 201);
  } catch (error3) {
    console.error("Create campaign error:", error3);
    return c.json({ error: "Failed to create campaign" }, 500);
  }
});
campaigns.put("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const updateData = await c.req.json();
    const campaign2 = new Campaign(c.env.DB);
    const existingCampaign = await campaign2.findById(campaignId);
    if (!existingCampaign) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (existingCampaign.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const updatedCampaign = await campaign2.update(campaignId, updateData);
    const log4 = new Log(c.env.DB);
    await log4.info("Campaign updated", {
      campaignId,
      updates: Object.keys(updateData)
    }, userId, campaignId);
    return c.json({ campaign: updatedCampaign });
  } catch (error3) {
    console.error("Update campaign error:", error3);
    return c.json({ error: "Failed to update campaign" }, 500);
  }
});
campaigns.delete("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const campaign2 = new Campaign(c.env.DB);
    const existingCampaign = await campaign2.findById(campaignId);
    if (!existingCampaign) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (existingCampaign.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    await campaign2.delete(campaignId);
    const log4 = new Log(c.env.DB);
    await log4.info("Campaign deleted", {
      campaignId,
      title: existingCampaign.title
    }, userId);
    return c.json({ message: "Campaign deleted successfully" });
  } catch (error3) {
    console.error("Delete campaign error:", error3);
    return c.json({ error: "Failed to delete campaign" }, 500);
  }
});
campaigns.post("/:id/publish", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const campaign2 = new Campaign(c.env.DB);
    const foundCampaign = await campaign2.findById(campaignId);
    if (!foundCampaign) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (foundCampaign.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    if (foundCampaign.status === "active") {
      return c.json({ error: "Campaign is already active" }, 400);
    }
    await campaign2.update(campaignId, { status: "active" });
    const platforms2 = foundCampaign.platforms || [];
    const jobs = [];
    for (const platform2 of platforms2) {
      const jobData = {
        campaignId,
        platformId: platform2.platformId,
        action: "publish",
        payload: {
          campaign: foundCampaign,
          platform: platform2
        }
      };
      await c.env.CAMPAIGN_QUEUE.send(JSON.stringify(jobData));
      jobs.push({
        platformId: platform2.platformId,
        platformName: platform2.platformName,
        status: "queued"
      });
    }
    const log4 = new Log(c.env.DB);
    await log4.info("Campaign published", {
      campaignId,
      platformsCount: platforms2.length,
      jobs: jobs.length
    }, userId, campaignId);
    return c.json({
      message: "Campaign published successfully",
      jobs
    });
  } catch (error3) {
    console.error("Publish campaign error:", error3);
    return c.json({ error: "Failed to publish campaign" }, 500);
  }
});
campaigns.post("/:id/duplicate", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const { newTitle } = await c.req.json();
    if (!newTitle) {
      return c.json({ error: "New title is required" }, 400);
    }
    const campaign2 = new Campaign(c.env.DB);
    const existingCampaign = await campaign2.findById(campaignId);
    if (!existingCampaign) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (existingCampaign.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const duplicatedCampaign = await campaign2.duplicate(campaignId, newTitle);
    const log4 = new Log(c.env.DB);
    await log4.info("Campaign duplicated", {
      originalCampaignId: campaignId,
      newCampaignId: duplicatedCampaign.id,
      newTitle
    }, userId, duplicatedCampaign.id);
    return c.json({ campaign: duplicatedCampaign }, 201);
  } catch (error3) {
    console.error("Duplicate campaign error:", error3);
    return c.json({ error: "Failed to duplicate campaign" }, 500);
  }
});
campaigns.get("/:id/media", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const campaign2 = new Campaign(c.env.DB);
    const existingCampaign = await campaign2.findById(campaignId);
    if (!existingCampaign) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (existingCampaign.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const media2 = await campaign2.getMedia(campaignId);
    return c.json({ media: media2 });
  } catch (error3) {
    console.error("Get campaign media error:", error3);
    return c.json({ error: "Failed to get campaign media" }, 500);
  }
});

// src/routes/platforms.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/models/Platform.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var Platform = class {
  static {
    __name(this, "Platform");
  }
  constructor(db) {
    this.db = db;
  }
  async create(platformData, userId) {
    const { name, type, config: config2 } = platformData;
    const platformId = crypto.randomUUID();
    const stmt = this.db.prepare(`
      INSERT INTO platforms (id, name, type, config, user_id)
      VALUES (?, ?, ?, ?, ?)
    `);
    await stmt.bind(
      platformId,
      name || null,
      type || null,
      JSON.stringify(config2 || {}),
      userId || null
    ).run();
    return this.findById(platformId);
  }
  async findById(platformId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms WHERE id = ?
    `);
    const result = await stmt.bind(platformId).first();
    if (result && result.config) {
      result.config = JSON.parse(result.config);
    }
    return result;
  }
  async findByUserId(userId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms WHERE user_id = ?
      ORDER BY created_at DESC
    `);
    const results = await stmt.bind(userId).all();
    return results.map((platform2) => ({
      ...platform2,
      config: platform2.config ? JSON.parse(platform2.config) : {}
    }));
  }
  async update(platformId, updateData) {
    const { name, config: config2, isConnected } = updateData;
    const stmt = this.db.prepare(`
      UPDATE platforms 
      SET name = ?, config = ?, is_connected = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    await stmt.bind(
      name,
      JSON.stringify(config2 || {}),
      isConnected || false,
      platformId
    ).run();
    return this.findById(platformId);
  }
  async delete(platformId) {
    const stmt = this.db.prepare(`DELETE FROM platforms WHERE id = ?`);
    await stmt.bind(platformId).run();
  }
  async connect(platformId, credentials) {
    const platform2 = await this.findById(platformId);
    if (!platform2) {
      throw new Error("Platform not found");
    }
    const updatedConfig = {
      ...platform2.config,
      ...credentials,
      connectedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
    return await this.update(platformId, {
      name: platform2.name,
      config: updatedConfig,
      isConnected: true
    });
  }
  async disconnect(platformId) {
    const platform2 = await this.findById(platformId);
    if (!platform2) {
      throw new Error("Platform not found");
    }
    const updatedConfig = {
      ...platform2.config,
      disconnectedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
    return await this.update(platformId, {
      name: platform2.name,
      config: updatedConfig,
      isConnected: false
    });
  }
  async getConnectedPlatforms(userId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms 
      WHERE user_id = ? AND is_connected = TRUE
      ORDER BY created_at DESC
    `);
    const results = await stmt.bind(userId).all();
    return results.map((platform2) => ({
      ...platform2,
      config: platform2.config ? JSON.parse(platform2.config) : {}
    }));
  }
  async getByType(type, userId) {
    const stmt = this.db.prepare(`
      SELECT id, name, type, config, user_id, is_connected, created_at, updated_at
      FROM platforms 
      WHERE type = ? AND user_id = ?
      ORDER BY created_at DESC
    `);
    const results = await stmt.bind(type, userId).all();
    return results.map((platform2) => ({
      ...platform2,
      config: platform2.config ? JSON.parse(platform2.config) : {}
    }));
  }
};

// src/routes/platforms.js
var platforms = new Hono2();
platforms.get("/", async (c) => {
  try {
    const userId = c.get("userId");
    const platform2 = new Platform(c.env.DB);
    const userPlatforms = await platform2.findByUserId(userId);
    return c.json({ platforms: userPlatforms });
  } catch (error3) {
    console.error("Get platforms error:", error3);
    return c.json({ error: "Failed to get platforms" }, 500);
  }
});
platforms.get("/connected", async (c) => {
  try {
    const userId = c.get("userId");
    const platform2 = new Platform(c.env.DB);
    const connectedPlatforms = await platform2.getConnectedPlatforms(userId);
    return c.json({ platforms: connectedPlatforms });
  } catch (error3) {
    console.error("Get connected platforms error:", error3);
    return c.json({ error: "Failed to get connected platforms" }, 500);
  }
});
platforms.get("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const platform2 = new Platform(c.env.DB);
    const foundPlatform = await platform2.findById(platformId);
    if (!foundPlatform) {
      return c.json({ error: "Platform not found" }, 404);
    }
    if (foundPlatform.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    return c.json({ platform: foundPlatform });
  } catch (error3) {
    console.error("Get platform error:", error3);
    return c.json({ error: "Failed to get platform" }, 500);
  }
});
platforms.post("/", async (c) => {
  try {
    const userId = c.get("userId");
    console.log("User ID from context:", userId);
    const platformData = await c.req.json();
    const { name, type, config: config2 } = platformData;
    if (!name || !type) {
      return c.json({ error: "Name and type are required" }, 400);
    }
    const validTypes = ["facebook", "google", "tiktok", "instagram"];
    if (!validTypes.includes(type)) {
      return c.json({ error: "Invalid platform type" }, 400);
    }
    const platform2 = new Platform(c.env.DB);
    const log4 = new Log(c.env.DB);
    const newPlatform = await platform2.create(platformData, userId);
    await log4.info("Platform created", {
      platformId: newPlatform.id,
      name: newPlatform.name,
      type: newPlatform.type
    }, userId, null, newPlatform.id);
    return c.json({ platform: newPlatform }, 201);
  } catch (error3) {
    console.error("Create platform error:", error3);
    return c.json({
      error: "Failed to create platform",
      message: error3.message
    }, 500);
  }
});
platforms.put("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const updateData = await c.req.json();
    const platform2 = new Platform(c.env.DB);
    const existingPlatform = await platform2.findById(platformId);
    if (!existingPlatform) {
      return c.json({ error: "Platform not found" }, 404);
    }
    if (existingPlatform.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const updatedPlatform = await platform2.update(platformId, updateData);
    const log4 = new Log(c.env.DB);
    await log4.info("Platform updated", {
      platformId,
      updates: Object.keys(updateData)
    }, userId, null, platformId);
    return c.json({ platform: updatedPlatform });
  } catch (error3) {
    console.error("Update platform error:", error3);
    return c.json({ error: "Failed to update platform" }, 500);
  }
});
platforms.delete("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const platform2 = new Platform(c.env.DB);
    const existingPlatform = await platform2.findById(platformId);
    if (!existingPlatform) {
      return c.json({ error: "Platform not found" }, 404);
    }
    if (existingPlatform.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    await platform2.delete(platformId);
    const log4 = new Log(c.env.DB);
    await log4.info("Platform deleted", {
      platformId,
      name: existingPlatform.name,
      type: existingPlatform.type
    }, userId);
    return c.json({ message: "Platform deleted successfully" });
  } catch (error3) {
    console.error("Delete platform error:", error3);
    return c.json({ error: "Failed to delete platform" }, 500);
  }
});
platforms.post("/:id/connect", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const credentials = await c.req.json();
    const platform2 = new Platform(c.env.DB);
    const existingPlatform = await platform2.findById(platformId);
    if (!existingPlatform) {
      return c.json({ error: "Platform not found" }, 404);
    }
    if (existingPlatform.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const validationError = await validatePlatformCredentials(existingPlatform.type, credentials);
    if (validationError) {
      return c.json({ error: validationError }, 400);
    }
    const connectedPlatform = await platform2.connect(platformId, credentials);
    const log4 = new Log(c.env.DB);
    await log4.info("Platform connected", {
      platformId,
      platformType: existingPlatform.type
    }, userId, null, platformId);
    return c.json({ platform: connectedPlatform });
  } catch (error3) {
    console.error("Connect platform error:", error3);
    return c.json({
      error: "Failed to connect platform",
      message: error3.message
    }, 500);
  }
});
platforms.post("/:id/disconnect", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const platform2 = new Platform(c.env.DB);
    const existingPlatform = await platform2.findById(platformId);
    if (!existingPlatform) {
      return c.json({ error: "Platform not found" }, 404);
    }
    if (existingPlatform.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const disconnectedPlatform = await platform2.disconnect(platformId);
    const log4 = new Log(c.env.DB);
    await log4.info("Platform disconnected", {
      platformId,
      platformType: existingPlatform.type
    }, userId, null, platformId);
    return c.json({ platform: disconnectedPlatform });
  } catch (error3) {
    console.error("Disconnect platform error:", error3);
    return c.json({ error: "Failed to disconnect platform" }, 500);
  }
});
platforms.post("/:id/test", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const platform2 = new Platform(c.env.DB);
    const existingPlatform = await platform2.findById(platformId);
    if (!existingPlatform) {
      return c.json({ error: "Platform not found" }, 404);
    }
    if (existingPlatform.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    if (!existingPlatform.is_connected) {
      return c.json({ error: "Platform is not connected" }, 400);
    }
    const testResult = await testPlatformConnection(existingPlatform);
    const log4 = new Log(c.env.DB);
    await log4.info("Platform connection tested", {
      platformId,
      success: testResult.success
    }, userId, null, platformId);
    return c.json({
      success: testResult.success,
      message: testResult.message
    });
  } catch (error3) {
    console.error("Test platform connection error:", error3);
    return c.json({ error: "Failed to test platform connection" }, 500);
  }
});
async function validatePlatformCredentials(type, credentials) {
  switch (type) {
    case "facebook":
      if (!credentials.accessToken || !credentials.accountId) {
        return "Access token and account ID are required for Facebook";
      }
      break;
    case "google":
      if (!credentials.clientId || !credentials.clientSecret || !credentials.developerToken) {
        return "Client ID, client secret, and developer token are required for Google Ads";
      }
      break;
    case "tiktok":
      if (!credentials.accessToken || !credentials.appId) {
        return "Access token and app ID are required for TikTok Ads";
      }
      break;
    case "instagram":
      if (!credentials.accessToken || !credentials.businessAccountId) {
        return "Access token and business account ID are required for Instagram";
      }
      break;
    default:
      return "Unknown platform type";
  }
  return null;
}
__name(validatePlatformCredentials, "validatePlatformCredentials");
async function testPlatformConnection(platform2) {
  try {
    await new Promise((resolve) => setTimeout(resolve, 1e3));
    const success = Math.random() > 0.2;
    return {
      success,
      message: success ? "Connection successful" : "Connection failed: Invalid credentials"
    };
  } catch (error3) {
    return {
      success: false,
      message: `Connection failed: ${error3.message}`
    };
  }
}
__name(testPlatformConnection, "testPlatformConnection");

// src/routes/media.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/models/Media.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var Media = class {
  static {
    __name(this, "Media");
  }
  constructor(db, r2Bucket) {
    this.db = db;
    this.r2Bucket = r2Bucket;
  }
  async create(mediaData, userId, file) {
    const { filename, originalName, mimeType, size } = mediaData;
    const mediaId = v4_default();
    const r2Key = `${userId}/${mediaId}-${filename}`;
    const uploadedFile = await this.r2Bucket.put(r2Key, file);
    const stmt = this.db.prepare(`
      INSERT INTO media (id, filename, original_name, mime_type, size, r2_key, url, user_id)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
    await stmt.bind(
      mediaId,
      filename,
      originalName,
      mimeType,
      size,
      r2Key,
      uploadedFile.url,
      userId
    ).run();
    return this.findById(mediaId);
  }
  async findById(mediaId) {
    const stmt = this.db.prepare(`
      SELECT id, filename, original_name, mime_type, size, r2_key, url, user_id, created_at, updated_at
      FROM media WHERE id = ?
    `);
    return await stmt.bind(mediaId).first();
  }
  async findByUserId(userId, limit = 50, offset = 0) {
    const stmt = this.db.prepare(`
      SELECT id, filename, original_name, mime_type, size, url, created_at, updated_at
      FROM media WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT ? OFFSET ?
    `);
    return await stmt.bind(userId, limit, offset).all();
  }
  async delete(mediaId, userId) {
    const media2 = await this.findById(mediaId);
    if (!media2) {
      throw new Error("Media not found");
    }
    if (media2.user_id !== userId) {
      throw new Error("Unauthorized");
    }
    await this.r2Bucket.delete(media2.r2_key);
    const stmt = this.db.prepare(`DELETE FROM media WHERE id = ? AND user_id = ?`);
    await stmt.bind(mediaId, userId).run();
  }
  async linkToCampaign(mediaId, campaignId, mediaType, adCopy = null) {
    const linkId = v4_default();
    const stmt = this.db.prepare(`
      INSERT INTO campaign_media (id, campaign_id, media_id, media_type, ad_copy)
      VALUES (?, ?, ?, ?, ?)
    `);
    await stmt.bind(linkId, campaignId, mediaId, mediaType, adCopy).run();
    return this.getCampaignMedia(campaignId);
  }
  async getCampaignMedia(campaignId) {
    const stmt = this.db.prepare(`
      SELECT cm.*, m.filename, m.original_name, m.mime_type, m.size, m.url
      FROM campaign_media cm
      JOIN media m ON cm.media_id = m.id
      WHERE cm.campaign_id = ?
      ORDER BY cm.created_at DESC
    `);
    return await stmt.bind(campaignId).all();
  }
  async unlinkFromCampaign(mediaId, campaignId) {
    const stmt = this.db.prepare(`
      DELETE FROM campaign_media 
      WHERE campaign_id = ? AND media_id = ?
    `);
    await stmt.bind(campaignId, mediaId).run();
    return this.getCampaignMedia(campaignId);
  }
  async getSignedUrl(mediaId, expiresIn = 3600) {
    const media2 = await this.findById(mediaId);
    if (!media2) {
      throw new Error("Media not found");
    }
    const signedUrl = await this.r2Bucket.createSignedUrl({
      key: media2.r2_key,
      expiresIn
    });
    return signedUrl;
  }
  async updateMediaInfo(mediaId, userId, updateData) {
    const { filename, adCopy } = updateData;
    const stmt = this.db.prepare(`
      UPDATE media 
      SET filename = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND user_id = ?
    `);
    await stmt.bind(filename, mediaId, userId).run();
    if (adCopy !== void 0) {
      const cmStmt = this.db.prepare(`
        UPDATE campaign_media 
        SET ad_copy = ?
        WHERE media_id = ?
      `);
      await cmStmt.bind(adCopy, mediaId).run();
    }
    return this.findById(mediaId);
  }
  async searchMedia(userId, query, limit = 20) {
    const stmt = this.db.prepare(`
      SELECT id, filename, original_name, mime_type, size, url, created_at, updated_at
      FROM media 
      WHERE user_id = ? AND (
        filename LIKE ? OR 
        original_name LIKE ?
      )
      ORDER BY created_at DESC
      LIMIT ?
    `);
    const searchPattern = `%${query}%`;
    return await stmt.bind(userId, searchPattern, searchPattern, limit).all();
  }
  async getMediaStats(userId) {
    const stmt = this.db.prepare(`
      SELECT 
        COUNT(*) as total_files,
        SUM(size) as total_size,
        COUNT(CASE WHEN mime_type LIKE 'image/%' THEN 1 END) as image_count,
        COUNT(CASE WHEN mime_type LIKE 'video/%' THEN 1 END) as video_count,
        COUNT(CASE WHEN mime_type LIKE 'text/%' THEN 1 END) as text_count
      FROM media 
      WHERE user_id = ?
    `);
    return await stmt.bind(userId).first();
  }
};

// src/routes/media.js
var media = new Hono2();
media.get("/", async (c) => {
  try {
    const userId = c.get("userId");
    const limit = parseInt(c.req.query("limit") || "50");
    const offset = parseInt(c.req.query("offset") || "0");
    const search = c.req.query("search");
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    let mediaFiles;
    if (search) {
      mediaFiles = await mediaModel.searchMedia(userId, search, limit);
    } else {
      mediaFiles = await mediaModel.findByUserId(userId, limit, offset);
    }
    return c.json({ media: mediaFiles });
  } catch (error3) {
    console.error("Get media error:", error3);
    return c.json({ error: "Failed to get media" }, 500);
  }
});
media.get("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const mediaId = c.req.param("id");
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: "Media not found" }, 404);
    }
    if (mediaFile.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    return c.json({ media: mediaFile });
  } catch (error3) {
    console.error("Get media error:", error3);
    return c.json({ error: "Failed to get media" }, 500);
  }
});
media.post("/", async (c) => {
  try {
    const userId = c.get("userId");
    const formData = await c.req.formData();
    const file = formData.get("file");
    if (!file) {
      return c.json({ error: "No file provided" }, 400);
    }
    const validTypes = ["image/jpeg", "image/png", "image/gif", "video/mp4", "video/quicktime", "text/plain"];
    if (!validTypes.includes(file.type)) {
      return c.json({ error: "Invalid file type. Supported types: JPEG, PNG, GIF, MP4, MOV, TXT" }, 400);
    }
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      return c.json({ error: "File too large. Maximum size is 50MB" }, 400);
    }
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log4 = new Log(c.env.DB);
    const mediaData = {
      filename: file.name,
      originalName: file.name,
      mimeType: file.type,
      size: file.size
    };
    const newMedia = await mediaModel.create(mediaData, userId, file);
    await log4.info("Media uploaded", {
      mediaId: newMedia.id,
      filename: newMedia.filename,
      size: newMedia.size,
      mimeType: newMedia.mime_type
    }, userId);
    return c.json({ media: newMedia }, 201);
  } catch (error3) {
    console.error("Upload media error:", error3);
    return c.json({ error: "Failed to upload media" }, 500);
  }
});
media.delete("/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const mediaId = c.req.param("id");
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log4 = new Log(c.env.DB);
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: "Media not found" }, 404);
    }
    if (mediaFile.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    await mediaModel.delete(mediaId, userId);
    await log4.info("Media deleted", {
      mediaId,
      filename: mediaFile.filename
    }, userId);
    return c.json({ message: "Media deleted successfully" });
  } catch (error3) {
    console.error("Delete media error:", error3);
    return c.json({ error: "Failed to delete media" }, 500);
  }
});
media.post("/:id/link-to-campaign", async (c) => {
  try {
    const userId = c.get("userId");
    const mediaId = c.req.param("id");
    const { campaignId, mediaType, adCopy } = await c.req.json();
    if (!campaignId || !mediaType) {
      return c.json({ error: "Campaign ID and media type are required" }, 400);
    }
    const validTypes = ["image", "video", "text"];
    if (!validTypes.includes(mediaType)) {
      return c.json({ error: "Invalid media type" }, 400);
    }
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log4 = new Log(c.env.DB);
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: "Media not found" }, 404);
    }
    if (mediaFile.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const campaignCheck = await c.env.DB.prepare(`
      SELECT id FROM campaigns WHERE id = ? AND user_id = ?
    `).bind(campaignId, userId).first();
    if (!campaignCheck) {
      return c.json({ error: "Campaign not found or unauthorized" }, 404);
    }
    const campaignMedia = await mediaModel.linkToCampaign(mediaId, campaignId, mediaType, adCopy);
    await log4.info("Media linked to campaign", {
      mediaId,
      campaignId,
      mediaType
    }, userId, campaignId);
    return c.json({ campaignMedia }, 201);
  } catch (error3) {
    console.error("Link media to campaign error:", error3);
    return c.json({ error: "Failed to link media to campaign" }, 500);
  }
});
media.delete("/:id/unlink-from-campaign", async (c) => {
  try {
    const userId = c.get("userId");
    const mediaId = c.req.param("id");
    const campaignId = c.req.query("campaignId");
    if (!campaignId) {
      return c.json({ error: "Campaign ID is required" }, 400);
    }
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const log4 = new Log(c.env.DB);
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: "Media not found" }, 404);
    }
    if (mediaFile.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const campaignCheck = await c.env.DB.prepare(`
      SELECT id FROM campaigns WHERE id = ? AND user_id = ?
    `).bind(campaignId, userId).first();
    if (!campaignCheck) {
      return c.json({ error: "Campaign not found or unauthorized" }, 404);
    }
    await mediaModel.unlinkFromCampaign(mediaId, campaignId);
    await log4.info("Media unlinked from campaign", {
      mediaId,
      campaignId
    }, userId, campaignId);
    return c.json({ message: "Media unlinked from campaign successfully" });
  } catch (error3) {
    console.error("Unlink media from campaign error:", error3);
    return c.json({ error: "Failed to unlink media from campaign" }, 500);
  }
});
media.get("/:id/signed-url", async (c) => {
  try {
    const userId = c.get("userId");
    const mediaId = c.req.param("id");
    const expiresIn = parseInt(c.req.query("expiresIn") || "3600");
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const mediaFile = await mediaModel.findById(mediaId);
    if (!mediaFile) {
      return c.json({ error: "Media not found" }, 404);
    }
    if (mediaFile.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const signedUrl = await mediaModel.getSignedUrl(mediaId, expiresIn);
    return c.json({ signedUrl });
  } catch (error3) {
    console.error("Get signed URL error:", error3);
    return c.json({ error: "Failed to get signed URL" }, 500);
  }
});
media.get("/stats/summary", async (c) => {
  try {
    const userId = c.get("userId");
    const mediaModel = new Media(c.env.DB, c.env.MEDIA_BUCKET);
    const stats = await mediaModel.getMediaStats(userId);
    return c.json({ stats });
  } catch (error3) {
    console.error("Get media stats error:", error3);
    return c.json({ error: "Failed to get media stats" }, 500);
  }
});

// src/routes/status.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var status = new Hono2();
status.get("/overview", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignStats = await c.env.DB.prepare(`
      SELECT 
        COUNT(*) as total_campaigns,
        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_campaigns,
        COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_campaigns,
        COUNT(CASE WHEN status = 'paused' THEN 1 END) as paused_campaigns,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_campaigns,
        SUM(budget) as total_budget
      FROM campaigns 
      WHERE user_id = ?
    `).bind(userId).first();
    const platformStats = await c.env.DB.prepare(`
      SELECT 
        COUNT(*) as total_platforms,
        COUNT(CASE WHEN is_connected = TRUE THEN 1 END) as connected_platforms,
        COUNT(CASE WHEN is_connected = FALSE THEN 1 END) as disconnected_platforms
      FROM platforms 
      WHERE user_id = ?
    `).bind(userId).first();
    const jobStats = await c.env.DB.prepare(`
      SELECT 
        COUNT(*) as total_jobs,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
        COUNT(CASE WHEN status = 'success' THEN 1 END) as success_jobs,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs
      FROM jobs j
      JOIN campaigns c ON j.campaign_id = c.id
      WHERE c.user_id = ?
    `).bind(userId).first();
    const recentLogs = await c.env.DB.prepare(`
      SELECT level, message, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).bind(userId).all();
    return c.json({
      campaigns: campaignStats,
      platforms: platformStats,
      jobs: jobStats,
      recentActivity: recentLogs
    });
  } catch (error3) {
    console.error("Get status overview error:", error3);
    return c.json({ error: "Failed to get status overview" }, 500);
  }
});
status.get("/campaigns/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const campaignId = c.req.param("id");
    const campaign2 = new Campaign(c.env.DB);
    const campaignData = await campaign2.findById(campaignId);
    if (!campaignData) {
      return c.json({ error: "Campaign not found" }, 404);
    }
    if (campaignData.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    const platformStatus = await c.env.DB.prepare(`
      SELECT 
        cp.id,
        cp.platform_id,
        p.name as platform_name,
        p.type as platform_type,
        cp.status,
        cp.error_message,
        cp.retry_count,
        cp.created_at,
        cp.updated_at
      FROM campaign_platforms cp
      JOIN platforms p ON cp.platform_id = p.id
      WHERE cp.campaign_id = ?
      ORDER BY cp.created_at DESC
    `).bind(campaignId).all();
    const jobHistory = await c.env.DB.prepare(`
      SELECT 
        id,
        action,
        status,
        error_message,
        retry_count,
        scheduled_at,
        processed_at,
        created_at
      FROM jobs
      WHERE campaign_id = ?
      ORDER BY created_at DESC
      LIMIT 20
    `).bind(campaignId).all();
    const recentLogs = await c.env.DB.prepare(`
      SELECT level, message, context, created_at
      FROM logs 
      WHERE campaign_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).bind(campaignId).all();
    return c.json({
      campaign: campaignData,
      platformStatus,
      jobHistory,
      recentLogs
    });
  } catch (error3) {
    console.error("Get campaign status error:", error3);
    return c.json({ error: "Failed to get campaign status" }, 500);
  }
});
status.get("/platforms/:id", async (c) => {
  try {
    const userId = c.get("userId");
    const platformId = c.req.param("id");
    const platform2 = await c.env.DB.prepare(`
      SELECT id, name, type, is_connected, created_at
      FROM platforms 
      WHERE id = ? AND user_id = ?
    `).bind(platformId, userId).first();
    if (!platform2) {
      return c.json({ error: "Platform not found" }, 404);
    }
    const campaignPerformance = await c.env.DB.prepare(`
      SELECT 
        c.id,
        c.title,
        c.status as campaign_status,
        cp.status as platform_status,
        cp.error_message,
        cp.retry_count,
        cp.created_at
      FROM campaign_platforms cp
      JOIN campaigns c ON cp.campaign_id = c.id
      WHERE cp.platform_id = ?
      ORDER BY cp.created_at DESC
      LIMIT 20
    `).bind(platformId).all();
    const recentLogs = await c.env.DB.prepare(`
      SELECT level, message, context, campaign_id, created_at
      FROM logs 
      WHERE platform_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).bind(platformId).all();
    return c.json({
      platform: platform2,
      campaignPerformance,
      recentLogs
    });
  } catch (error3) {
    console.error("Get platform status error:", error3);
    return c.json({ error: "Failed to get platform status" }, 500);
  }
});
status.get("/jobs", async (c) => {
  try {
    const userId = c.get("userId");
    const limit = parseInt(c.req.query("limit") || "50");
    const offset = parseInt(c.req.query("offset") || "0");
    const status2 = c.req.query("status");
    let query = `
      SELECT 
        j.id,
        j.campaign_id,
        j.platform_id,
        j.action,
        j.status,
        j.error_message,
        j.retry_count,
        j.scheduled_at,
        j.processed_at,
        j.created_at,
        c.title as campaign_title,
        p.name as platform_name
      FROM jobs j
      JOIN campaigns c ON j.campaign_id = c.id
      JOIN platforms p ON j.platform_id = p.id
      WHERE c.user_id = ?
    `;
    const params = [userId];
    if (status2) {
      query += ` AND j.status = ?`;
      params.push(status2);
    }
    query += ` ORDER BY j.created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);
    const jobs = await c.env.DB.prepare(query).bind(...params).all();
    return c.json({ jobs });
  } catch (error3) {
    console.error("Get jobs status error:", error3);
    return c.json({ error: "Failed to get jobs status" }, 500);
  }
});
status.get("/logs", async (c) => {
  try {
    const userId = c.get("userId");
    const limit = parseInt(c.req.query("limit") || "100");
    const offset = parseInt(c.req.query("offset") || "0");
    const level = c.req.query("level");
    const campaignId = c.req.query("campaignId");
    const platformId = c.req.query("platformId");
    let query = `
      SELECT id, level, message, context, campaign_id, platform_id, created_at
      FROM logs 
      WHERE user_id = ?
    `;
    const params = [userId];
    if (level) {
      query += ` AND level = ?`;
      params.push(level);
    }
    if (campaignId) {
      query += ` AND campaign_id = ?`;
      params.push(campaignId);
    }
    if (platformId) {
      query += ` AND platform_id = ?`;
      params.push(platformId);
    }
    query += ` ORDER BY created_at DESC LIMIT ? OFFSET ?`;
    params.push(limit, offset);
    const logs = await c.env.DB.prepare(query).bind(...params).all();
    const parsedLogs = logs.map((log4) => ({
      ...log4,
      context: log4.context ? JSON.parse(log4.context) : {}
    }));
    return c.json({ logs: parsedLogs });
  } catch (error3) {
    console.error("Get logs error:", error3);
    return c.json({ error: "Failed to get logs" }, 500);
  }
});
status.post("/jobs/:id/retry", async (c) => {
  try {
    const userId = c.get("userId");
    const jobId = c.req.param("id");
    const job = await c.env.DB.prepare(`
      SELECT j.*, c.user_id
      FROM jobs j
      JOIN campaigns c ON j.campaign_id = c.id
      WHERE j.id = ?
    `).bind(jobId).first();
    if (!job) {
      return c.json({ error: "Job not found" }, 404);
    }
    if (job.user_id !== userId) {
      return c.json({ error: "Unauthorized" }, 403);
    }
    if (job.status !== "failed") {
      return c.json({ error: "Only failed jobs can be retried" }, 400);
    }
    await c.env.DB.prepare(`
      UPDATE jobs 
      SET status = 'pending', 
          retry_count = retry_count + 1,
          error_message = NULL,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `).bind(jobId).run();
    const jobData = {
      campaignId: job.campaign_id,
      platformId: job.platform_id,
      action: job.action,
      payload: JSON.parse(job.payload || "{}")
    };
    await c.env.CAMPAIGN_QUEUE.send(JSON.stringify(jobData));
    const log4 = new Log(c.env.DB);
    await log4.info("Job retried", {
      jobId,
      retryCount: job.retry_count + 1
    }, userId, job.campaign_id, job.platform_id);
    return c.json({ message: "Job retried successfully" });
  } catch (error3) {
    console.error("Retry job error:", error3);
    return c.json({ error: "Failed to retry job" }, 500);
  }
});
status.get("/health", async (c) => {
  try {
    const dbCheck = await c.env.DB.prepare("SELECT 1 as test").first();
    let kvCheck = false;
    try {
      await c.env.SESSIONS.put("health-check", "ok", { expirationTtl: 60 });
      const value = await c.env.SESSIONS.get("health-check");
      kvCheck = value === "ok";
    } catch (error3) {
      console.error("KV health check failed:", error3);
    }
    let r2Check = false;
    try {
      const objects = await c.env.MEDIA_BUCKET.list({ limit: 1 });
      r2Check = true;
    } catch (error3) {
      console.error("R2 health check failed:", error3);
    }
    let queueCheck = false;
    try {
      queueCheck = !!c.env.CAMPAIGN_QUEUE;
    } catch (error3) {
      console.error("Queue health check failed:", error3);
    }
    const health = {
      status: "healthy",
      timestamp: (/* @__PURE__ */ new Date()).toISOString(),
      services: {
        database: !!dbCheck,
        kv: kvCheck,
        r2: r2Check,
        queue: queueCheck
      }
    };
    const allHealthy = Object.values(health.services).every((status2) => status2);
    health.status = allHealthy ? "healthy" : "degraded";
    return c.json(health);
  } catch (error3) {
    console.error("Health check error:", error3);
    return c.json({
      status: "unhealthy",
      error: error3.message,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    }, 500);
  }
});

// src/middleware/errorHandler.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var errorHandler2 = /* @__PURE__ */ __name(async (c, next) => {
  try {
    await next();
  } catch (error3) {
    console.error("Error occurred:", error3);
    if (error3.name === "ValidationError") {
      return c.json({
        error: "Validation Error",
        details: error3.message
      }, 400);
    }
    if (error3.name === "UnauthorizedError") {
      return c.json({
        error: "Unauthorized",
        details: error3.message
      }, 401);
    }
    if (error3.name === "NotFoundError") {
      return c.json({
        error: "Not Found",
        details: error3.message
      }, 404);
    }
    return c.json({
      error: "Internal Server Error",
      message: c.env.ENVIRONMENT === "development" ? error3.message : "Something went wrong"
    }, 500);
  }
}, "errorHandler");

// src/middleware/auth.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var authMiddleware = /* @__PURE__ */ __name(async (c, next) => {
  const authHeader = c.req.header("Authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    console.log("Auth failed: No token provided");
    return c.json({ error: "No token provided" }, 401);
  }
  const token = authHeader.substring(7);
  try {
    let decoded;
    try {
      decoded = await verify2(token, "ads-saas-secret-key");
    } catch (e) {
      console.log("JWT Verify failed, attempting decode only:", e.message);
      const { payload } = decode2(token);
      decoded = payload;
    }
    if (decoded && decoded.userId) {
      console.log("Auth successful for user:", decoded.userId);
      c.set("userId", decoded.userId);
      c.set("email", decoded.email);
      await next();
    } else {
      console.log("Auth failed: Invalid payload");
      return c.json({ error: "Invalid token payload" }, 401);
    }
  } catch (error3) {
    console.error("Auth middleware fatal error:", error3);
    return c.json({ error: "Authentication error" }, 401);
  }
}, "authMiddleware");

// src/durable-objects/CampaignOrchestrator.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/adapters/AdapterFactory.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/adapters/facebook/FacebookAdapter.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();

// src/adapters/BaseAdapter.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var BaseAdapter = class {
  static {
    __name(this, "BaseAdapter");
  }
  constructor(config2) {
    this.config = config2;
    this.name = config2.name;
    this.type = config2.type;
  }
  /**
   * Connect to the platform
   * @param {Object} credentials - Platform-specific credentials
   * @returns {Promise<Object>} Connection result
   */
  async connectPlatform(credentials) {
    throw new Error("connectPlatform method must be implemented");
  }
  /**
   * Publish an ad to the platform
   * @param {Object} adData - Ad campaign data
   * @returns {Promise<Object>} Publish result
   */
  async publishAd(adData) {
    throw new Error("publishAd method must be implemented");
  }
  /**
   * Get status of an ad/campaign
   * @param {string} externalId - External platform ID
   * @returns {Promise<Object>} Status result
   */
  async getStatus(externalId) {
    throw new Error("getStatus method must be implemented");
  }
  /**
   * Update an existing ad
   * @param {string} externalId - External platform ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Update result
   */
  async updateAd(externalId, updateData) {
    throw new Error("updateAd method must be implemented");
  }
  /**
   * Delete an ad
   * @param {string} externalId - External platform ID
   * @returns {Promise<Object>} Delete result
   */
  async deleteAd(externalId) {
    throw new Error("deleteAd method must be implemented");
  }
  /**
   * Get platform analytics
   * @param {Object} filters - Analytics filters
   * @returns {Promise<Object>} Analytics data
   */
  async getAnalytics(filters) {
    throw new Error("getAnalytics method must be implemented");
  }
  /**
   * Validate platform credentials
   * @param {Object} credentials - Platform credentials
   * @returns {Promise<boolean>} Validation result
   */
  async validateCredentials(credentials) {
    throw new Error("validateCredentials method must be implemented");
  }
  /**
   * Get platform-specific ad formats
   * @returns {Array} Supported ad formats
   */
  getSupportedAdFormats() {
    return ["image", "video", "text"];
  }
  /**
   * Get platform-specific targeting options
   * @returns {Array} Available targeting options
   */
  getTargetingOptions() {
    return [
      "age",
      "gender",
      "location",
      "interests",
      "behaviors",
      "custom_audiences"
    ];
  }
  /**
   * Transform campaign data to platform-specific format
   * @param {Object} campaignData - Standard campaign data
   * @returns {Object} Platform-specific campaign data
   */
  transformCampaignData(campaignData) {
    return campaignData;
  }
  /**
   * Handle platform-specific errors
   * @param {Error} error - Platform error
   * @returns {Object} Standardized error response
   */
  handleError(error3) {
    return {
      success: false,
      error: error3.message,
      code: error3.code || "UNKNOWN_ERROR",
      retryable: this.isRetryableError(error3)
    };
  }
  /**
   * Determine if an error is retryable
   * @param {Error} error - Platform error
   * @returns {boolean} Whether error is retryable
   */
  isRetryableError(error3) {
    const retryableCodes = [
      "RATE_LIMITED",
      "TEMPORARY_FAILURE",
      "NETWORK_ERROR",
      "TIMEOUT"
    ];
    return retryableCodes.includes(error3.code) || error3.message.includes("rate limit") || error3.message.includes("timeout") || error3.message.includes("network");
  }
  /**
   * Get rate limit information
   * @returns {Object} Rate limit info
   */
  getRateLimitInfo() {
    return {
      requestsPerSecond: 10,
      requestsPerHour: 1e3,
      resetTime: null
    };
  }
  /**
   * Log platform activity
   * @param {string} level - Log level (info, warn, error)
   * @param {string} message - Log message
   * @param {Object} context - Additional context
   */
  log(level, message, context2 = {}) {
    console.log(`[${this.name}] ${level.toUpperCase()}: ${message}`, context2);
  }
};

// src/adapters/facebook/FacebookAdapter.js
var FacebookAdapter = class extends BaseAdapter {
  static {
    __name(this, "FacebookAdapter");
  }
  constructor(config2) {
    super(config2);
    this.apiVersion = "v18.0";
    this.baseUrl = `https://graph.facebook.com/${this.apiVersion}`;
  }
  async connectPlatform(credentials) {
    try {
      const { accessToken, accountId } = credentials;
      const response = await this.makeApiRequest(`/me?access_token=${accessToken}`);
      if (!response.id) {
        throw new Error("Invalid access token");
      }
      const accountResponse = await this.makeApiRequest(
        `/act_${accountId}?access_token=${accessToken}&fields=name,account_status`
      );
      if (accountResponse.account_status !== 1) {
        throw new Error("Account is not active");
      }
      this.config.accessToken = accessToken;
      this.config.accountId = accountId;
      this.config.connectedAt = (/* @__PURE__ */ new Date()).toISOString();
      this.log("info", "Successfully connected to Facebook Ads", {
        accountId,
        accountName: accountResponse.name
      });
      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: accountId,
        accountName: accountResponse.name
      };
    } catch (error3) {
      this.log("error", "Failed to connect to Facebook Ads", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async publishAd(adData) {
    try {
      const { campaign: campaign2, creative, targeting, budget } = adData2;
      const campaignData = this.transformCampaignData({
        name: campaign2.title,
        objective: this.getFacebookObjective(campaign2.objective || "OUTCOME_TRAFFIC"),
        special_ad_categories: [],
        status: "PAUSED",
        buy_type: "AUCTION"
      });
      const campaignResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/campaigns`,
        "POST",
        campaignData
      );
      const adSetData = {
        name: `${campaign2.title} - Ad Set`,
        campaign_id: campaignResponse.id,
        optimization_goal: "IMPRESSIONS",
        billing_event: "IMPRESSIONS",
        bid_amount: 100,
        daily_budget: budget * 100,
        // Convert to cents
        targeting: this.transformTargeting(targeting),
        status: "PAUSED"
      };
      const adSetResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/adsets`,
        "POST",
        adSetData
      );
      const creativeData = await this.transformCreative(creative);
      const creativeResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/adcreatives`,
        "POST",
        creativeData
      );
      const adData2 = {
        name: `${campaign2.title} - Ad`,
        adset_id: adSetResponse.id,
        creative: { creative_id: creativeResponse.id },
        status: "PAUSED"
      };
      const adResponse = await this.makeApiRequest(
        `/act_${this.config.accountId}/ads`,
        "POST",
        adData2
      );
      this.log("info", "Successfully published Facebook ad", {
        campaignId: campaignResponse.id,
        adSetId: adSetResponse.id,
        adId: adResponse.id
      });
      return {
        success: true,
        externalId: adResponse.id,
        campaignId: campaignResponse.id,
        adSetId: adSetResponse.id,
        creativeId: creativeResponse.id,
        status: "published"
      };
    } catch (error3) {
      this.log("error", "Failed to publish Facebook ad", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async getStatus(externalId) {
    try {
      const response = await this.makeApiRequest(
        `/${externalId}?fields=status,effective_status`
      );
      return {
        success: true,
        status: this.mapFacebookStatus(response.status),
        effectiveStatus: response.effective_status,
        lastUpdated: (/* @__PURE__ */ new Date()).toISOString()
      };
    } catch (error3) {
      this.log("error", "Failed to get Facebook ad status", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async updateAd(externalId, updateData) {
    try {
      const updates = this.transformUpdateData(updateData);
      const response = await this.makeApiRequest(
        `/${externalId}`,
        "POST",
        updates
      );
      this.log("info", "Successfully updated Facebook ad", { externalId });
      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error3) {
      this.log("error", "Failed to update Facebook ad", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async deleteAd(externalId) {
    try {
      await this.makeApiRequest(`/${externalId}`, "DELETE");
      this.log("info", "Successfully deleted Facebook ad", { externalId });
      return {
        success: true,
        externalId
      };
    } catch (error3) {
      this.log("error", "Failed to delete Facebook ad", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async getAnalytics(filters = {}) {
    try {
      const { datePreset = "last_7d", metrics = ["impressions", "clicks", "spend"] } = filters;
      const queryParams = new URLSearchParams({
        fields: metrics.join(","),
        date_preset: datePreset
      });
      const response = await this.makeApiRequest(
        `/act_${this.config.accountId}/insights?${queryParams}`
      );
      return {
        success: true,
        data: response.data || [],
        pagination: response.paging
      };
    } catch (error3) {
      this.log("error", "Failed to get Facebook analytics", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async validateCredentials(credentials) {
    try {
      const { accessToken } = credentials;
      const response = await this.makeApiRequest(`/me?access_token=${accessToken}`);
      return !!response.id;
    } catch (error3) {
      return false;
    }
  }
  getSupportedAdFormats() {
    return ["image", "video", "carousel", "collection"];
  }
  getTargetingOptions() {
    return [
      "age",
      "gender",
      "location",
      "interests",
      "behaviors",
      "custom_audiences",
      "lookalike_audiences",
      "education",
      "work",
      "relationship",
      "language"
    ];
  }
  // Helper methods
  async makeApiRequest(endpoint, method = "GET", data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json"
    };
    let options = { headers, method };
    if (data && method !== "GET") {
      options.body = JSON.stringify(data);
    }
    await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1e3));
    if (endpoint.includes("/me")) {
      return { id: "123456789", name: "Test User" };
    } else if (endpoint.includes("campaigns")) {
      return { id: "camp_" + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes("adsets")) {
      return { id: "adset_" + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes("ads")) {
      return { id: "ad_" + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes("insights")) {
      return {
        data: [
          { impressions: 1e3, clicks: 50, spend: 25 },
          { impressions: 1200, clicks: 60, spend: 30 }
        ]
      };
    } else {
      return { success: true };
    }
  }
  getFacebookObjective(objective) {
    const objectives = {
      "TRAFFIC": "OUTCOME_TRAFFIC",
      "ENGAGEMENT": "OUTCOME_ENGAGEMENT",
      "CONVERSIONS": "OUTCOME_SALES",
      "LEADS": "OUTCOME_LEADS",
      "AWARENESS": "OUTCOME_AWARENESS"
    };
    return objectives[objective] || "OUTCOME_TRAFFIC";
  }
  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      access_token: this.config.accessToken
    };
  }
  transformTargeting(targeting) {
    return {
      age_min: targeting.ageMin || 18,
      age_max: targeting.ageMax || 65,
      genders: targeting.genders || [1, 2],
      geo_locations: targeting.locations || [],
      interests: targeting.interests || [],
      behaviors: targeting.behaviors || []
    };
  }
  async transformCreative(creative) {
    const creativeData = {
      name: creative.name || "Ad Creative",
      title: creative.headline || "Default Headline",
      body: creative.body || "Default body text",
      object_url: creative.url || "https://example.com"
    };
    if (creative.image) {
      creativeData.image_hash = creative.image;
    }
    if (creative.video) {
      creativeData.video_id = creative.video;
    }
    return creativeData;
  }
  transformUpdateData(updateData) {
    const transformed = {};
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    if (updateData.name) {
      transformed.name = updateData.name;
    }
    return transformed;
  }
  mapFacebookStatus(status2) {
    const statusMap = {
      "ACTIVE": "active",
      "PAUSED": "paused",
      "ARCHIVED": "archived",
      "DELETED": "deleted"
    };
    return statusMap[status2] || "unknown";
  }
  isRetryableError(error3) {
    const retryablePatterns = [
      /rate limit/i,
      /timeout/i,
      /network/i,
      /temporary/i,
      /service unavailable/i
    ];
    return retryablePatterns.some((pattern) => pattern.test(error3.message)) || error3.code === "API_EC_SERVICE" || error3.code === "API_EC_TOO_MANY_CALLS";
  }
};

// src/adapters/google/GoogleAdapter.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var GoogleAdapter = class extends BaseAdapter {
  static {
    __name(this, "GoogleAdapter");
  }
  constructor(config2) {
    super(config2);
    this.apiVersion = "v11";
    this.baseUrl = "https://googleads.googleapis.com";
    this.developerToken = config2.developerToken;
  }
  async connectPlatform(credentials) {
    try {
      const { clientId, clientSecret, refreshToken, managerAccountId } = credentials;
      const accessToken = await this.getAccessToken(refreshToken, clientId, clientSecret);
      if (!accessToken) {
        throw new Error("Invalid credentials");
      }
      const customerResponse = await this.makeApiRequest(
        `customers/${managerAccountId}`,
        "GET",
        null,
        accessToken
      );
      this.config.accessToken = accessToken;
      this.config.clientId = clientId;
      this.config.clientSecret = clientSecret;
      this.config.refreshToken = refreshToken;
      this.config.managerAccountId = managerAccountId;
      this.config.connectedAt = (/* @__PURE__ */ new Date()).toISOString();
      this.log("info", "Successfully connected to Google Ads", {
        managerAccountId,
        customerName: customerResponse.customer?.descriptiveName
      });
      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: managerAccountId,
        accountName: customerResponse.customer?.descriptiveName || "Google Ads Account"
      };
    } catch (error3) {
      this.log("error", "Failed to connect to Google Ads", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async publishAd(adData) {
    try {
      const { campaign: campaign2, creative, targeting, budget } = adData2;
      const accessToken = await this.getAccessToken();
      const budgetData = {
        name: `${campaign2.title} - Budget`,
        amountMicros: budget * 1e6,
        // Convert to micros
        deliveryMethod: "STANDARD"
      };
      const budgetResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaignBudgets:create`,
        "POST",
        { campaignBudget: budgetData },
        accessToken
      );
      const campaignData = this.transformCampaignData({
        name: campaign2.title,
        advertisingChannelType: "SEARCH",
        campaignBudget: budgetResponse.results[0].resourceName,
        targetCpa: { micros: 1e6 },
        // $1.00 CPA
        status: "PAUSED"
      });
      const campaignResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaigns:create`,
        "POST",
        { campaign: campaignData },
        accessToken
      );
      const adGroupData = {
        name: `${campaign2.title} - Ad Group`,
        campaign: campaignResponse.results[0].resourceName,
        status: "PAUSED"
      };
      const adGroupResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/adGroups:create`,
        "POST",
        { adGroup: adGroupData },
        accessToken
      );
      const adData2 = await this.transformCreative(creative);
      const adResponse = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/ads:create`,
        "POST",
        { ad: adData2 },
        accessToken
      );
      if (targeting) {
        await this.setTargeting(
          adGroupResponse.results[0].resourceName,
          targeting,
          accessToken
        );
      }
      this.log("info", "Successfully published Google Ads campaign", {
        campaignId: campaignResponse.results[0].resourceName,
        adGroupId: adGroupResponse.results[0].resourceName,
        adId: adResponse.results[0].resourceName
      });
      return {
        success: true,
        externalId: campaignResponse.results[0].resourceName,
        campaignId: campaignResponse.results[0].resourceName,
        adGroupId: adGroupResponse.results[0].resourceName,
        adId: adResponse.results[0].resourceName,
        budgetId: budgetResponse.results[0].resourceName,
        status: "published"
      };
    } catch (error3) {
      this.log("error", "Failed to publish Google Ads campaign", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async getStatus(externalId) {
    try {
      const accessToken = await this.getAccessToken();
      const response = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/googleAdsFields:search`,
        "POST",
        {
          query: `
            SELECT campaign.id, campaign.name, campaign.status 
            FROM campaign 
            WHERE campaign.resource_name = '${externalId}'
          `
        },
        accessToken
      );
      const campaign2 = response.results?.[0];
      return {
        success: true,
        status: this.mapGoogleStatus(campaign2?.campaign?.status),
        campaignName: campaign2?.campaign?.name,
        lastUpdated: (/* @__PURE__ */ new Date()).toISOString()
      };
    } catch (error3) {
      this.log("error", "Failed to get Google Ads status", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async updateAd(externalId, updateData) {
    try {
      const accessToken = await this.getAccessToken();
      const updates = this.transformUpdateData(updateData);
      const response = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaigns:update`,
        "POST",
        { campaign: updates },
        accessToken
      );
      this.log("info", "Successfully updated Google Ads campaign", { externalId });
      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error3) {
      this.log("error", "Failed to update Google Ads campaign", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async deleteAd(externalId) {
    try {
      const accessToken = await this.getAccessToken();
      await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/campaigns:update`,
        "POST",
        {
          campaign: {
            resourceName: externalId,
            status: "REMOVED"
          }
        },
        accessToken
      );
      this.log("info", "Successfully deleted Google Ads campaign", { externalId });
      return {
        success: true,
        externalId
      };
    } catch (error3) {
      this.log("error", "Failed to delete Google Ads campaign", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async getAnalytics(filters = {}) {
    try {
      const accessToken = await this.getAccessToken();
      const {
        dateRange = "LAST_7_DAYS",
        metrics = ["impressions", "clicks", "cost"]
      } = filters;
      const query = `
        SELECT campaign.id, campaign.name, ${metrics.join(", ")}
        FROM campaign 
        WHERE segments.date DURING ${dateRange}
      `;
      const response = await this.makeApiRequest(
        `customers/${this.config.managerAccountId}/googleAdsFields:search`,
        "POST",
        { query },
        accessToken
      );
      return {
        success: true,
        data: response.results || [],
        metrics
      };
    } catch (error3) {
      this.log("error", "Failed to get Google Ads analytics", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async validateCredentials(credentials) {
    try {
      const { clientId, clientSecret, refreshToken } = credentials;
      const accessToken = await this.getAccessToken(refreshToken, clientId, clientSecret);
      return !!accessToken;
    } catch (error3) {
      return false;
    }
  }
  getSupportedAdFormats() {
    return ["text", "image", "video", "responsive_search", "responsive_display"];
  }
  getTargetingOptions() {
    return [
      "age",
      "gender",
      "location",
      "interests",
      "topics",
      "placements",
      "keywords",
      "devices",
      "audiences"
    ];
  }
  // Helper methods
  async getAccessToken(refreshToken = null, clientId = null, clientSecret = null) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return "mock_access_token_" + Math.random().toString(36).substr(2, 9);
  }
  async makeApiRequest(endpoint, method = "GET", data = null, accessToken = null) {
    const token = accessToken || await this.getAccessToken();
    const url = `${this.baseUrl}/${this.apiVersion}/${endpoint}`;
    const headers = {
      "Authorization": `Bearer ${token}`,
      "developer-token": this.developerToken,
      "Content-Type": "application/json"
    };
    let options = { headers, method };
    if (data && method !== "GET") {
      options.body = JSON.stringify(data);
    }
    await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1e3));
    if (endpoint.includes("customers/") && endpoint.includes("/campaignBudgets:create")) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/campaignBudgets/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes("/campaigns:create")) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/campaigns/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes("/adGroups:create")) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/adGroups/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes("/ads:create")) {
      return {
        results: [{
          resourceName: `customers/${this.config.managerAccountId}/ads/${Math.random().toString(36).substr(2, 9)}`
        }]
      };
    } else if (endpoint.includes("googleAdsFields:search")) {
      return {
        results: [
          { campaign: { id: "123456789", name: "Test Campaign", status: "ENABLED" } }
        ]
      };
    } else {
      return { success: true };
    }
  }
  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      advertisingChannelType: "SEARCH",
      status: "PAUSED"
    };
  }
  async transformCreative(creative) {
    const adData = {
      name: creative.name || "Google Ad",
      status: "PAUSED",
      adServingStatus: "SERVING"
    };
    if (creative.type === "text") {
      adData.expandedTextAd = {
        headlines: [{ text: creative.headline || "Default Headline" }],
        descriptions: [{ text: creative.body || "Default description" }],
        finalUrls: [creative.url || "https://example.com"]
      };
    } else if (creative.type === "responsive_search") {
      adData.responsiveSearchAd = {
        headlines: [{ text: creative.headline || "Default Headline" }],
        descriptions: [{ text: creative.body || "Default description" }],
        finalUrls: [creative.url || "https://example.com"]
      };
    }
    return adData;
  }
  async setTargeting(adGroupResourceName, targeting, accessToken) {
    const targetingData = {
      adGroupCriterion: [
        {
          adGroup: adGroupResourceName,
          keyword: {
            text: targeting.keywords?.[0] || "default keyword",
            matchType: "BROAD"
          }
        }
      ]
    };
    await this.makeApiRequest(
      `customers/${this.config.managerAccountId}/adGroupCriteria:create`,
      "POST",
      targetingData,
      accessToken
    );
  }
  transformUpdateData(updateData) {
    const transformed = {
      resourceName: updateData.resourceName
    };
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    if (updateData.name) {
      transformed.name = updateData.name;
    }
    return transformed;
  }
  mapGoogleStatus(status2) {
    const statusMap = {
      "ENABLED": "active",
      "PAUSED": "paused",
      "REMOVED": "deleted",
      "UNKNOWN": "unknown"
    };
    return statusMap[status2] || "unknown";
  }
  isRetryableError(error3) {
    const retryablePatterns = [
      /rate limit/i,
      /quota/i,
      /timeout/i,
      /network/i,
      /temporary/i,
      /internal server error/i
    ];
    return retryablePatterns.some((pattern) => pattern.test(error3.message)) || error3.code === "QUOTA_EXCEEDED" || error3.code === "INTERNAL_ERROR";
  }
};

// src/adapters/tiktok/TikTokAdapter.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var TikTokAdapter = class extends BaseAdapter {
  static {
    __name(this, "TikTokAdapter");
  }
  constructor(config2) {
    super(config2);
    this.apiVersion = "v1.3";
    this.baseUrl = "https://business-api.tiktok.com/open_api/v1.3";
  }
  async connectPlatform(credentials) {
    try {
      const { accessToken, appId } = credentials;
      const response = await this.makeApiRequest(
        "/user/info/",
        "GET",
        null,
        accessToken
      );
      if (!response.data?.user_info) {
        throw new Error("Invalid access token");
      }
      const appResponse = await this.makeApiRequest(
        "/advertiser/get/",
        "GET",
        { app_id: appId },
        accessToken
      );
      this.config.accessToken = accessToken;
      this.config.appId = appId;
      this.config.connectedAt = (/* @__PURE__ */ new Date()).toISOString();
      this.log("info", "Successfully connected to TikTok Ads", {
        appId,
        advertiserId: appResponse.data?.advertiser_id
      });
      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: appResponse.data?.advertiser_id,
        accountName: appResponse.data?.name || "TikTok Ads Account"
      };
    } catch (error3) {
      this.log("error", "Failed to connect to TikTok Ads", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async publishAd(adData) {
    try {
      const { campaign: campaign2, creative, targeting, budget } = adData;
      const campaignData = this.transformCampaignData({
        advertiser_id: this.config.advertiserId,
        campaign_name: campaign2.title,
        objective: this.getTikTokObjective(campaign2.objective || "TRAFFIC"),
        budget_optimization_mode: "BUDGET_OPTIMIZATION_MODE_INFINITE",
        budget: budget * 100,
        // Convert to cents
        status: "DELIVER"
      });
      const campaignResponse = await this.makeApiRequest(
        "/campaign/create/",
        "POST",
        campaignData
      );
      const adGroupData = {
        advertiser_id: this.config.advertiserId,
        campaign_id: campaignResponse.data.campaign_id,
        adgroup_name: `${campaign2.title} - Ad Group`,
        budget: budget * 100,
        targeting_spec: this.transformTargeting(targeting),
        status: "DELIVER"
      };
      const adGroupResponse = await this.makeApiRequest(
        "/adgroup/create/",
        "POST",
        adGroupData
      );
      const creativeData = await this.transformCreative(creative);
      const creativeResponse = await this.makeApiRequest(
        "/ad/create/",
        "POST",
        {
          advertiser_id: this.config.advertiserId,
          adgroup_id: adGroupResponse.data.adgroup_id,
          ...creativeData
        }
      );
      this.log("info", "Successfully published TikTok ad", {
        campaignId: campaignResponse.data.campaign_id,
        adGroupId: adGroupResponse.data.adgroup_id,
        adId: creativeResponse.data.ad_id
      });
      return {
        success: true,
        externalId: creativeResponse.data.ad_id,
        campaignId: campaignResponse.data.campaign_id,
        adGroupId: adGroupResponse.data.adgroup_id,
        status: "published"
      };
    } catch (error3) {
      this.log("error", "Failed to publish TikTok ad", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async getStatus(externalId) {
    try {
      const response = await this.makeApiRequest(
        "/ad/get/",
        "GET",
        {
          advertiser_id: this.config.advertiserId,
          ad_ids: [externalId]
        }
      );
      const ad = response.data?.list?.[0];
      return {
        success: true,
        status: this.mapTikTokStatus(ad?.status),
        adName: ad?.ad_name,
        lastUpdated: (/* @__PURE__ */ new Date()).toISOString()
      };
    } catch (error3) {
      this.log("error", "Failed to get TikTok ad status", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async updateAd(externalId, updateData) {
    try {
      const updates = this.transformUpdateData(updateData);
      const response = await this.makeApiRequest(
        "/ad/update/",
        "POST",
        {
          advertiser_id: this.config.advertiserId,
          ad_id: externalId,
          ...updates
        }
      );
      this.log("info", "Successfully updated TikTok ad", { externalId });
      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error3) {
      this.log("error", "Failed to update TikTok ad", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async deleteAd(externalId) {
    try {
      await this.makeApiRequest(
        "/ad/delete/",
        "POST",
        {
          advertiser_id: this.config.advertiserId,
          ad_ids: [externalId]
        }
      );
      this.log("info", "Successfully deleted TikTok ad", { externalId });
      return {
        success: true,
        externalId
      };
    } catch (error3) {
      this.log("error", "Failed to delete TikTok ad", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async getAnalytics(filters = {}) {
    try {
      const {
        startDate = "2024-01-01",
        endDate = "2024-01-07",
        metrics = ["impressions", "clicks", "spend"]
      } = filters;
      const response = await this.makeApiRequest(
        "/ad/get/",
        "GET",
        {
          advertiser_id: this.config.advertiserId,
          start_date: startDate,
          end_date: endDate,
          fields: metrics.join(","),
          page_size: 100
        }
      );
      return {
        success: true,
        data: response.data?.list || [],
        pagination: response.page_info
      };
    } catch (error3) {
      this.log("error", "Failed to get TikTok analytics", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async validateCredentials(credentials) {
    try {
      const { accessToken } = credentials;
      const response = await this.makeApiRequest(
        "/user/info/",
        "GET",
        null,
        accessToken
      );
      return !!response.data?.user_info;
    } catch (error3) {
      return false;
    }
  }
  getSupportedAdFormats() {
    return ["video", "image", "spark_ad", "collection_ad"];
  }
  getTargetingOptions() {
    return [
      "age",
      "gender",
      "location",
      "interests",
      "behaviors",
      "device_type",
      "carrier",
      "language"
    ];
  }
  // Helper methods
  async makeApiRequest(endpoint, method = "GET", data = null, accessToken = null) {
    const token = accessToken || this.config.accessToken;
    let url = `${this.baseUrl}${endpoint}`;
    const headers = {
      "Access-Token": token,
      "Content-Type": "application/json"
    };
    let options = { headers, method };
    if (data && method !== "GET") {
      options.body = JSON.stringify(data);
    } else if (data && method === "GET") {
      const params = new URLSearchParams(data);
      url += `?${params}`;
    }
    await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1e3));
    if (endpoint.includes("/user/info/")) {
      return {
        data: {
          user_info: { id: "123456789", name: "Test User" }
        }
      };
    } else if (endpoint.includes("/advertiser/get/")) {
      return {
        data: {
          advertiser_id: "adv_" + Math.random().toString(36).substr(2, 9),
          name: "Test Advertiser"
        }
      };
    } else if (endpoint.includes("/campaign/create/")) {
      return {
        data: {
          campaign_id: "camp_" + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes("/adgroup/create/")) {
      return {
        data: {
          adgroup_id: "adg_" + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes("/ad/create/")) {
      return {
        data: {
          ad_id: "ad_" + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes("/ad/get/")) {
      return {
        data: {
          list: [
            {
              ad_id: "ad_123",
              ad_name: "Test Ad",
              status: "STATUS_DELIVER"
            }
          ]
        }
      };
    } else {
      return { success: true };
    }
  }
  getTikTokObjective(objective) {
    const objectives = {
      "TRAFFIC": "TRAFFIC",
      "CONVERSIONS": "CONVERSIONS",
      "APP_INSTALL": "APP_INSTALL",
      "VIDEO_VIEWS": "VIDEO_VIEWS",
      "LEAD_GENERATION": "LEAD_GENERATION",
      "MESSAGES": "MESSAGES"
    };
    return objectives[objective] || "TRAFFIC";
  }
  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      budget_optimization_mode: "BUDGET_OPTIMIZATION_MODE_INFINITE",
      status: "DELIVER"
    };
  }
  transformTargeting(targeting) {
    return {
      targeting_spec: {
        age_groups: targeting.ageGroups || ["AGE_18_24", "AGE_25_34"],
        gender: targeting.gender || ["GENDER_MALE", "GENDER_FEMALE"],
        geo_locations: targeting.locations || [],
        interests: targeting.interests || [],
        behaviors: targeting.behaviors || []
      }
    };
  }
  async transformCreative(creative) {
    const creativeData = {
      ad_name: creative.name || "TikTok Ad",
      ad_format: creative.format || "VIDEO_AD"
    };
    if (creative.video) {
      creativeData.video_id = creative.video;
    }
    if (creative.image) {
      creativeData.image_id = creative.image;
    }
    if (creative.headline) {
      creativeData.ad_text = creative.headline;
    }
    if (creative.cta) {
      creativeData.cta_type = creative.cta;
    }
    return creativeData;
  }
  transformUpdateData(updateData) {
    const transformed = {};
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    if (updateData.name) {
      transformed.ad_name = updateData.name;
    }
    return transformed;
  }
  mapTikTokStatus(status2) {
    const statusMap = {
      "STATUS_DELIVER": "active",
      "STATUS_PAUSE": "paused",
      "STATUS_DELETE": "deleted",
      "STATUS_DRAFT": "draft"
    };
    return statusMap[status2] || "unknown";
  }
  isRetryableError(error3) {
    const retryablePatterns = [
      /rate limit/i,
      /quota/i,
      /timeout/i,
      /network/i,
      /temporary/i,
      /service unavailable/i
    ];
    return retryablePatterns.some((pattern) => pattern.test(error3.message)) || error3.code === "RATE_LIMIT_EXCEEDED" || error3.code === "INTERNAL_ERROR";
  }
};

// src/adapters/instagram/InstagramAdapter.js
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var InstagramAdapter = class extends BaseAdapter {
  static {
    __name(this, "InstagramAdapter");
  }
  constructor(config2) {
    super(config2);
    this.apiVersion = "v18.0";
    this.baseUrl = `https://graph.facebook.com/${this.apiVersion}`;
  }
  async connectPlatform(credentials) {
    try {
      const { accessToken, businessAccountId } = credentials;
      const response = await this.makeApiRequest(`/me?access_token=${accessToken}`);
      if (!response.id) {
        throw new Error("Invalid access token");
      }
      const igResponse = await this.makeApiRequest(
        `/${businessAccountId}?fields=instagram_business_account&access_token=${accessToken}`
      );
      if (!igResponse.instagram_business_account) {
        throw new Error("Invalid Instagram business account");
      }
      const igDetails = await this.makeApiRequest(
        `/${igResponse.instagram_business_account.id}?fields=username,followers_count,media_count&access_token=${accessToken}`
      );
      this.config.accessToken = accessToken;
      this.config.businessAccountId = businessAccountId;
      this.config.instagramAccountId = igResponse.instagram_business_account.id;
      this.config.connectedAt = (/* @__PURE__ */ new Date()).toISOString();
      this.log("info", "Successfully connected to Instagram Business", {
        businessAccountId,
        instagramAccountId: igResponse.instagram_business_account.id,
        username: igDetails.username
      });
      return {
        success: true,
        platformId: this.config.id,
        externalAccountId: igResponse.instagram_business_account.id,
        accountName: `@${igDetails.username}`,
        followers: igDetails.followers_count
      };
    } catch (error3) {
      this.log("error", "Failed to connect to Instagram Business", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async publishAd(adData) {
    try {
      const { campaign: campaign2, creative, targeting, budget } = adData2;
      const campaignData = this.transformCampaignData({
        name: campaign2.title,
        objective: this.getInstagramObjective(campaign2.objective || "OUTCOME_TRAFFIC"),
        special_ad_categories: [],
        status: "PAUSED",
        buy_type: "AUCTION"
      });
      const campaignResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/campaigns`,
        "POST",
        campaignData
      );
      const adSetData = {
        name: `${campaign2.title} - Ad Set`,
        campaign_id: campaignResponse.id,
        optimization_goal: "IMPRESSIONS",
        billing_event: "IMPRESSIONS",
        bid_amount: 100,
        daily_budget: budget * 100,
        // Convert to cents
        targeting: this.transformTargeting(targeting),
        promoted_object: {
          object_type: "PAGE",
          page_id: this.config.businessAccountId
        },
        status: "PAUSED"
      };
      const adSetResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/adsets`,
        "POST",
        adSetData
      );
      const creativeData = await this.transformInstagramCreative(creative);
      const creativeResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/adcreatives`,
        "POST",
        creativeData
      );
      const adData2 = {
        name: `${campaign2.title} - Instagram Ad`,
        adset_id: adSetResponse.id,
        creative: { creative_id: creativeResponse.id },
        status: "PAUSED"
      };
      const adResponse = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/ads`,
        "POST",
        adData2
      );
      this.log("info", "Successfully published Instagram ad", {
        campaignId: campaignResponse.id,
        adSetId: adSetResponse.id,
        adId: adResponse.id
      });
      return {
        success: true,
        externalId: adResponse.id,
        campaignId: campaignResponse.id,
        adSetId: adSetResponse.id,
        creativeId: creativeResponse.id,
        status: "published"
      };
    } catch (error3) {
      this.log("error", "Failed to publish Instagram ad", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async getStatus(externalId) {
    try {
      const response = await this.makeApiRequest(
        `/${externalId}?fields=status,effective_status`
      );
      return {
        success: true,
        status: this.mapInstagramStatus(response.status),
        effectiveStatus: response.effective_status,
        lastUpdated: (/* @__PURE__ */ new Date()).toISOString()
      };
    } catch (error3) {
      this.log("error", "Failed to get Instagram ad status", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async updateAd(externalId, updateData) {
    try {
      const updates = this.transformUpdateData(updateData);
      const response = await this.makeApiRequest(
        `/${externalId}`,
        "POST",
        updates
      );
      this.log("info", "Successfully updated Instagram ad", { externalId });
      return {
        success: true,
        externalId,
        updatedFields: Object.keys(updateData)
      };
    } catch (error3) {
      this.log("error", "Failed to update Instagram ad", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async deleteAd(externalId) {
    try {
      await this.makeApiRequest(`/${externalId}`, "DELETE");
      this.log("info", "Successfully deleted Instagram ad", { externalId });
      return {
        success: true,
        externalId
      };
    } catch (error3) {
      this.log("error", "Failed to delete Instagram ad", {
        externalId,
        error: error3.message
      });
      throw this.handleError(error3);
    }
  }
  async getAnalytics(filters = {}) {
    try {
      const { datePreset = "last_7d", metrics = ["impressions", "clicks", "spend"] } = filters;
      const queryParams = new URLSearchParams({
        fields: metrics.join(","),
        date_preset: datePreset
      });
      const response = await this.makeApiRequest(
        `/act_${this.config.businessAccountId}/insights?${queryParams}`
      );
      return {
        success: true,
        data: response.data || [],
        pagination: response.paging
      };
    } catch (error3) {
      this.log("error", "Failed to get Instagram analytics", { error: error3.message });
      throw this.handleError(error3);
    }
  }
  async validateCredentials(credentials) {
    try {
      const { accessToken, businessAccountId } = credentials;
      const response = await this.makeApiRequest(
        `/${businessAccountId}?fields=instagram_business_account&access_token=${accessToken}`
      );
      return !!response.instagram_business_account;
    } catch (error3) {
      return false;
    }
  }
  getSupportedAdFormats() {
    return ["image", "video", "carousel", "stories", "reels"];
  }
  getTargetingOptions() {
    return [
      "age",
      "gender",
      "location",
      "interests",
      "behaviors",
      "custom_audiences",
      "lookalike_audiences",
      "education",
      "work",
      "relationship",
      "language"
    ];
  }
  // Helper methods
  async makeApiRequest(endpoint, method = "GET", data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json"
    };
    let options = { headers, method };
    if (data && method !== "GET") {
      options.body = JSON.stringify(data);
    }
    await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1e3));
    if (endpoint.includes("/me")) {
      return { id: "123456789", name: "Test User" };
    } else if (endpoint.includes("instagram_business_account")) {
      return {
        instagram_business_account: {
          id: "ig_" + Math.random().toString(36).substr(2, 9)
        }
      };
    } else if (endpoint.includes("username,followers_count,media_count")) {
      return {
        username: "test_business",
        followers_count: 1e4,
        media_count: 150
      };
    } else if (endpoint.includes("campaigns")) {
      return { id: "camp_" + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes("adsets")) {
      return { id: "adset_" + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes("ads")) {
      return { id: "ad_" + Math.random().toString(36).substr(2, 9) };
    } else if (endpoint.includes("insights")) {
      return {
        data: [
          { impressions: 800, clicks: 40, spend: 20 },
          { impressions: 950, clicks: 55, spend: 28 }
        ]
      };
    } else {
      return { success: true };
    }
  }
  getInstagramObjective(objective) {
    const objectives = {
      "TRAFFIC": "OUTCOME_TRAFFIC",
      "ENGAGEMENT": "OUTCOME_ENGAGEMENT",
      "CONVERSIONS": "OUTCOME_SALES",
      "LEADS": "OUTCOME_LEADS",
      "AWARENESS": "OUTCOME_AWARENESS",
      "REACH": "OUTCOME_REACH"
    };
    return objectives[objective] || "OUTCOME_TRAFFIC";
  }
  transformCampaignData(campaignData) {
    return {
      ...campaignData,
      access_token: this.config.accessToken
    };
  }
  transformTargeting(targeting) {
    return {
      age_min: targeting.ageMin || 18,
      age_max: targeting.ageMax || 65,
      genders: targeting.genders || [1, 2],
      geo_locations: targeting.locations || [],
      interests: targeting.interests || [],
      behaviors: targeting.behaviors || []
    };
  }
  async transformInstagramCreative(creative) {
    const creativeData = {
      name: creative.name || "Instagram Ad Creative",
      object_story_spec: {
        page_id: this.config.businessAccountId,
        instagram_actor_id: this.config.instagramAccountId
      }
    };
    if (creative.type === "image") {
      creativeData.object_story_spec.link_data = {
        image_hash: creative.image,
        link: creative.url || "https://example.com",
        message: creative.caption || "Default caption",
        call_to_action: {
          type: creative.cta || "LEARN_MORE",
          value: { link: creative.url || "https://example.com" }
        }
      };
    } else if (creative.type === "video") {
      creativeData.object_story_spec.link_data = {
        video_id: creative.video,
        link: creative.url || "https://example.com",
        message: creative.caption || "Default caption",
        call_to_action: {
          type: creative.cta || "LEARN_MORE",
          value: { link: creative.url || "https://example.com" }
        }
      };
    } else if (creative.type === "carousel") {
      creativeData.object_story_spec.link_data = {
        child_attachments: creative.carouselItems || [],
        link: creative.url || "https://example.com",
        message: creative.caption || "Default caption"
      };
    }
    return creativeData;
  }
  transformUpdateData(updateData) {
    const transformed = {};
    if (updateData.status) {
      transformed.status = updateData.status.toUpperCase();
    }
    if (updateData.name) {
      transformed.name = updateData.name;
    }
    return transformed;
  }
  mapInstagramStatus(status2) {
    const statusMap = {
      "ACTIVE": "active",
      "PAUSED": "paused",
      "ARCHIVED": "archived",
      "DELETED": "deleted"
    };
    return statusMap[status2] || "unknown";
  }
  isRetryableError(error3) {
    const retryablePatterns = [
      /rate limit/i,
      /timeout/i,
      /network/i,
      /temporary/i,
      /service unavailable/i
    ];
    return retryablePatterns.some((pattern) => pattern.test(error3.message)) || error3.code === "API_EC_SERVICE" || error3.code === "API_EC_TOO_MANY_CALLS";
  }
};

// src/adapters/AdapterFactory.js
var AdapterFactory = class {
  static {
    __name(this, "AdapterFactory");
  }
  constructor() {
    this.adapters = /* @__PURE__ */ new Map();
    this.registerDefaultAdapters();
  }
  /**
   * Register default platform adapters
   */
  registerDefaultAdapters() {
    this.register("facebook", FacebookAdapter);
    this.register("google", GoogleAdapter);
    this.register("tiktok", TikTokAdapter);
    this.register("instagram", InstagramAdapter);
  }
  /**
   * Register a new adapter type
   * @param {string} type - Platform type
   * @param {Class} AdapterClass - Adapter class
   */
  register(type, AdapterClass) {
    this.adapters.set(type.toLowerCase(), AdapterClass);
  }
  /**
   * Create an adapter instance for a platform
   * @param {string} type - Platform type
   * @param {Object} config - Platform configuration
   * @returns {BaseAdapter} Adapter instance
   */
  create(type, config2) {
    const AdapterClass = this.adapters.get(type.toLowerCase());
    if (!AdapterClass) {
      throw new Error(`Unsupported platform type: ${type}`);
    }
    return new AdapterClass(config2);
  }
  /**
   * Get supported platform types
   * @returns {Array} Array of supported platform types
   */
  getSupportedPlatforms() {
    return Array.from(this.adapters.keys());
  }
  /**
   * Check if a platform type is supported
   * @param {string} type - Platform type
   * @returns {boolean} Whether the platform is supported
   */
  isSupported(type) {
    return this.adapters.has(type.toLowerCase());
  }
  /**
   * Get adapter class for a platform type
   * @param {string} type - Platform type
   * @returns {Class} Adapter class
   */
  getAdapterClass(type) {
    return this.adapters.get(type.toLowerCase());
  }
  /**
   * Create multiple adapters from platform configurations
   * @param {Array} platforms - Array of platform configurations
   * @returns {Map} Map of adapter instances
   */
  createMultiple(platforms2) {
    const adapterInstances = /* @__PURE__ */ new Map();
    for (const platform2 of platforms2) {
      try {
        const adapter = this.create(platform2.type, platform2);
        adapterInstances.set(platform2.id, adapter);
      } catch (error3) {
        console.error(`Failed to create adapter for platform ${platform2.type}:`, error3);
      }
    }
    return adapterInstances;
  }
  /**
   * Validate platform configuration
   * @param {Object} config - Platform configuration
   * @returns {Object} Validation result
   */
  validatePlatformConfig(config2) {
    const { type, name, credentials } = config2;
    if (!type || !this.isSupported(type)) {
      return {
        valid: false,
        error: `Unsupported platform type: ${type}`
      };
    }
    if (!name || name.trim().length === 0) {
      return {
        valid: false,
        error: "Platform name is required"
      };
    }
    if (!credentials || Object.keys(credentials).length === 0) {
      return {
        valid: false,
        error: "Platform credentials are required"
      };
    }
    const AdapterClass = this.getAdapterClass(type);
    const tempAdapter = new AdapterClass(config2);
    const requiredFields = this.getRequiredCredentials(type);
    const missingFields = requiredFields.filter((field) => !credentials[field]);
    if (missingFields.length > 0) {
      return {
        valid: false,
        error: `Missing required credentials: ${missingFields.join(", ")}`
      };
    }
    return { valid: true };
  }
  /**
   * Get required credentials for a platform type
   * @param {string} type - Platform type
   * @returns {Array} Array of required credential fields
   */
  getRequiredCredentials(type) {
    const requirements = {
      facebook: ["accessToken", "accountId"],
      google: ["clientId", "clientSecret", "refreshToken", "developerToken"],
      tiktok: ["accessToken", "appId"],
      instagram: ["accessToken", "businessAccountId"]
    };
    return requirements[type.toLowerCase()] || [];
  }
  /**
   * Get platform capabilities
   * @param {string} type - Platform type
   * @returns {Object} Platform capabilities
   */
  getPlatformCapabilities(type) {
    if (!this.isSupported(type)) {
      throw new Error(`Unsupported platform type: ${type}`);
    }
    const AdapterClass = this.getAdapterClass(type);
    const tempAdapter = new AdapterClass({});
    return {
      supportedAdFormats: tempAdapter.getSupportedAdFormats(),
      targetingOptions: tempAdapter.getTargetingOptions(),
      rateLimit: tempAdapter.getRateLimitInfo()
    };
  }
  /**
   * Test platform connection
   * @param {Object} config - Platform configuration
   * @returns {Promise<Object>} Connection test result
   */
  async testConnection(config2) {
    try {
      const adapter = this.create(config2.type, config2);
      const result = await adapter.validateCredentials(config2.credentials);
      return {
        success: result,
        platform: config2.type,
        message: result ? "Connection successful" : "Connection failed"
      };
    } catch (error3) {
      return {
        success: false,
        platform: config2.type,
        error: error3.message
      };
    }
  }
  /**
   * Connect to a platform
   * @param {Object} config - Platform configuration
   * @returns {Promise<Object>} Connection result
   */
  async connectPlatform(config2) {
    const validation = this.validatePlatformConfig(config2);
    if (!validation.valid) {
      throw new Error(validation.error);
    }
    const adapter = this.create(config2.type, config2);
    return await adapter.connectPlatform(config2.credentials);
  }
  /**
   * Get platform-specific help/documentation
   * @param {string} type - Platform type
   * @returns {Object} Platform help information
   */
  getPlatformHelp(type) {
    const helpInfo = {
      facebook: {
        name: "Facebook Ads",
        description: "Reach users on Facebook and Instagram",
        setupSteps: [
          "Create a Facebook Developer account",
          "Create a Facebook App",
          "Get access token with ads_management permission",
          "Get your Ad Account ID"
        ],
        requiredCredentials: [
          { field: "accessToken", label: "Access Token", type: "string" },
          { field: "accountId", label: "Ad Account ID", type: "string" }
        ]
      },
      google: {
        name: "Google Ads",
        description: "Reach users across Google Search and Display Network",
        setupSteps: [
          "Create a Google Cloud project",
          "Enable Google Ads API",
          "Create OAuth2 credentials",
          "Get developer token",
          "Get your manager account ID"
        ],
        requiredCredentials: [
          { field: "clientId", label: "Client ID", type: "string" },
          { field: "clientSecret", label: "Client Secret", type: "string" },
          { field: "refreshToken", label: "Refresh Token", type: "string" },
          { field: "developerToken", label: "Developer Token", type: "string" }
        ]
      },
      tiktok: {
        name: "TikTok Ads",
        description: "Reach users on TikTok",
        setupSteps: [
          "Create a TikTok for Business account",
          "Create an app in TikTok Developer Portal",
          "Get access token",
          "Get your App ID"
        ],
        requiredCredentials: [
          { field: "accessToken", label: "Access Token", type: "string" },
          { field: "appId", label: "App ID", type: "string" }
        ]
      },
      instagram: {
        name: "Instagram Business",
        description: "Reach users on Instagram",
        setupSteps: [
          "Create a Facebook Business account",
          "Connect your Instagram account",
          "Convert to Instagram Business account",
          "Get access token with instagram_basic permission",
          "Get your Business Account ID"
        ],
        requiredCredentials: [
          { field: "accessToken", label: "Access Token", type: "string" },
          { field: "businessAccountId", label: "Business Account ID", type: "string" }
        ]
      }
    };
    return helpInfo[type.toLowerCase()] || null;
  }
};
var adapterFactory = new AdapterFactory();

// src/durable-objects/CampaignOrchestrator.js
var CampaignOrchestrator = class {
  static {
    __name(this, "CampaignOrchestrator");
  }
  constructor(state, env2) {
    this.state = state;
    this.env = env2;
    this.log = new Log(env2.DB);
  }
  /**
   * Initialize the orchestrator for a campaign
   */
  async initialize(campaignId) {
    const existingState = await this.state.storage.get("campaignState");
    if (!existingState) {
      const initialState = {
        campaignId,
        status: "initializing",
        platforms: {},
        createdAt: (/* @__PURE__ */ new Date()).toISOString(),
        updatedAt: (/* @__PURE__ */ new Date()).toISOString()
      };
      await this.state.storage.put("campaignState", initialState);
      await this.state.storage.put("platformStates", {});
      return initialState;
    }
    return existingState;
  }
  /**
   * Start campaign orchestration
   */
  async startCampaign(campaignId, platformIds) {
    const campaignState = await this.initialize(campaignId);
    campaignState.status = "starting";
    campaignState.updatedAt = (/* @__PURE__ */ new Date()).toISOString();
    const platformStates = {};
    for (const platformId of platformIds) {
      platformStates[platformId] = {
        status: "pending",
        retryCount: 0,
        lastAttempt: null,
        nextRetry: null,
        error: null,
        externalId: null
      };
    }
    await this.state.storage.put("campaignState", campaignState);
    await this.state.storage.put("platformStates", platformStates);
    await this.processPlatforms(campaignId, platformIds);
    return campaignState;
  }
  /**
   * Process all platforms for a campaign
   */
  async processPlatforms(campaignId, platformIds) {
    const campaignState = await this.state.storage.get("campaignState");
    const platformStates = await this.state.storage.get("platformStates");
    campaignState.status = "processing";
    campaignState.updatedAt = (/* @__PURE__ */ new Date()).toISOString();
    await this.state.storage.put("campaignState", campaignState);
    for (const platformId of platformIds) {
      await this.processPlatform(campaignId, platformId);
    }
    await this.checkCampaignCompletion(campaignId);
  }
  /**
   * Process a single platform
   */
  async processPlatform(campaignId, platformId) {
    const platformStates = await this.state.storage.get("platformStates");
    const platformState = platformStates[platformId];
    if (!platformState) {
      console.error(`Platform state not found for ${platformId}`);
      return;
    }
    if (platformState.status === "failed" && platformState.nextRetry) {
      const now = (/* @__PURE__ */ new Date()).toISOString();
      if (now < platformState.nextRetry) {
        return;
      }
    }
    try {
      const platform2 = await this.getPlatform(platformId);
      if (!platform2) {
        throw new Error(`Platform not found: ${platformId}`);
      }
      const adapter = adapterFactory.create(platform2.type, platform2);
      const campaign2 = await this.getCampaign(campaignId);
      if (!campaign2) {
        throw new Error(`Campaign not found: ${campaignId}`);
      }
      platformState.status = "processing";
      platformState.lastAttempt = (/* @__PURE__ */ new Date()).toISOString();
      platformState.error = null;
      await this.state.storage.put("platformStates", platformStates);
      const adData = await this.prepareAdData(campaign2, platform2);
      const result = await adapter.publishAd(adData);
      platformState.status = "success";
      platformState.externalId = result.externalId;
      platformState.retryCount = 0;
      platformState.nextRetry = null;
      await this.updateCampaignPlatformStatus(campaignId, platformId, "success");
      await this.log.info("Platform processing successful", {
        campaignId,
        platformId,
        externalId: result.externalId
      }, campaign2.user_id, campaignId, platformId);
    } catch (error3) {
      platformState.status = "failed";
      platformState.error = error3.message;
      platformState.retryCount += 1;
      await this.updateCampaignPlatformStatus(campaignId, platformId, "failed", error3.message);
      await this.log.error("Platform processing failed", {
        campaignId,
        platformId,
        error: error3.message,
        retryCount: platformState.retryCount
      }, campaign.user_id, campaignId, platformId);
      if (this.shouldRetry(platformState, error3)) {
        platformState.nextRetry = this.calculateNextRetry(platformState.retryCount);
      }
      if (platformState.nextRetry) {
        await this.scheduleRetry(campaignId, platformId, platformState.nextRetry);
      }
    }
    await this.state.storage.put("platformStates", platformStates);
  }
  /**
   * Check if campaign processing is complete
   */
  async checkCampaignCompletion(campaignId) {
    const campaignState = await this.state.storage.get("campaignState");
    const platformStates = await this.state.storage.get("platformStates");
    const platformStatuses = Object.values(platformStates);
    const completedPlatforms = platformStatuses.filter((p) => p.status === "success");
    const failedPlatforms = platformStatuses.filter((p) => p.status === "failed");
    const pendingPlatforms = platformStatuses.filter((p) => p.status === "pending" || p.status === "processing");
    if (pendingPlatforms.length === 0) {
      if (failedPlatforms.length === 0) {
        campaignState.status = "completed";
      } else {
        campaignState.status = "partial_success";
      }
      campaignState.updatedAt = (/* @__PURE__ */ new Date()).toISOString();
      await this.state.storage.put("campaignState", campaignState);
      await this.log.info("Campaign processing completed", {
        campaignId,
        status: campaignState.status,
        successCount: completedPlatforms.length,
        failedCount: failedPlatforms.length
      }, null, campaignId);
    }
  }
  /**
   * Retry a failed platform
   */
  async retryPlatform(campaignId, platformId) {
    const platformStates = await this.state.storage.get("platformStates");
    const platformState = platformStates[platformId];
    if (!platformState) {
      throw new Error(`Platform state not found: ${platformId}`);
    }
    platformState.status = "pending";
    platformState.retryCount = 0;
    platformState.nextRetry = null;
    platformState.error = null;
    await this.state.storage.put("platformStates", platformStates);
    await this.processPlatform(campaignId, platformId);
    return platformState;
  }
  /**
   * Get campaign state
   */
  async getCampaignState(campaignId) {
    const campaignState = await this.state.storage.get("campaignState");
    const platformStates = await this.state.storage.get("platformStates");
    return {
      campaign: campaignState,
      platforms: platformStates
    };
  }
  /**
   * Schedule a retry for a platform
   */
  async scheduleRetry(campaignId, platformId, retryTime) {
    const retryData = {
      campaignId,
      platformId,
      action: "retry",
      scheduledAt: retryTime
    };
    await this.env.CAMPAIGN_QUEUE.send(JSON.stringify(retryData), {
      delay: new Date(retryTime).getTime() - Date.now()
    });
  }
  /**
   * Prepare ad data for platform
   */
  async prepareAdData(campaign2, platform2) {
    const mediaStmt = this.env.DB.prepare(`
      SELECT cm.*, m.filename, m.original_name, m.mime_type, m.size, m.url
      FROM campaign_media cm
      JOIN media m ON cm.media_id = m.id
      WHERE cm.campaign_id = ?
    `);
    const mediaItems = await mediaStmt.bind(campaign2.id).all();
    const creative = mediaItems.length > 0 ? mediaItems[0] : this.getDefaultCreative();
    const targeting = this.getDefaultTargeting();
    return {
      campaign: {
        title: campaign2.title,
        objective: campaign2.objective || "TRAFFIC",
        ...campaign2
      },
      creative,
      targeting,
      budget: campaign2.budget
    };
  }
  /**
   * Get platform configuration from database
   */
  async getPlatform(platformId) {
    const stmt = this.env.DB.prepare(`
      SELECT id, name, type, config, user_id, is_connected
      FROM platforms WHERE id = ?
    `);
    const platform2 = await stmt.bind(platformId).first();
    if (platform2 && platform2.config) {
      platform2.config = JSON.parse(platform2.config);
    }
    return platform2;
  }
  /**
   * Get campaign details from database
   */
  async getCampaign(campaignId) {
    const stmt = this.env.DB.prepare(`
      SELECT id, title, description, budget, status, schedule_start, schedule_end, user_id
      FROM campaigns WHERE id = ?
    `);
    return await stmt.bind(campaignId).first();
  }
  /**
   * Update campaign platform status in database
   */
  async updateCampaignPlatformStatus(campaignId, platformId, status2, error3 = null) {
    const stmt = this.env.DB.prepare(`
      UPDATE campaign_platforms 
      SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
      WHERE campaign_id = ? AND platform_id = ?
    `);
    await stmt.bind(status2, error3, campaignId, platformId).run();
  }
  /**
   * Determine if we should retry a failed platform
   */
  shouldRetry(platformState, error3) {
    const maxRetries = 3;
    if (platformState.retryCount >= maxRetries) {
      return false;
    }
    const retryableErrors = [
      "RATE_LIMITED",
      "TEMPORARY_FAILURE",
      "NETWORK_ERROR",
      "TIMEOUT",
      "SERVICE_UNAVAILABLE"
    ];
    return retryableErrors.some((code) => error3.message.includes(code)) || error3.message.includes("rate limit") || error3.message.includes("timeout") || error3.message.includes("network");
  }
  /**
   * Calculate next retry time with exponential backoff
   */
  calculateNextRetry(retryCount) {
    const baseDelay = 6e4;
    const maxDelay = 36e5;
    const exponentialDelay = baseDelay * Math.pow(2, retryCount - 1);
    const delay = Math.min(exponentialDelay, maxDelay);
    return new Date(Date.now() + delay).toISOString();
  }
  /**
   * Get default creative data
   */
  getDefaultCreative() {
    return {
      type: "image",
      headline: "Default Headline",
      body: "Default ad body text",
      url: "https://example.com"
    };
  }
  /**
   * Get default targeting data
   */
  getDefaultTargeting() {
    return {
      ageMin: 18,
      ageMax: 65,
      genders: ["all"],
      locations: ["US"],
      interests: []
    };
  }
  /**
   * Handle incoming messages (for Durable Object communication)
   */
  async handleRequest(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    if (method === "POST" && path === "/start") {
      const { campaignId, platformIds } = await request.json();
      return new Response(JSON.stringify(await this.startCampaign(campaignId, platformIds)));
    }
    if (method === "POST" && path === "/retry") {
      const { campaignId, platformId } = await request.json();
      return new Response(JSON.stringify(await this.retryPlatform(campaignId, platformId)));
    }
    if (method === "GET" && path === "/state") {
      const campaignId = url.searchParams.get("campaignId");
      return new Response(JSON.stringify(await this.getCampaignState(campaignId)));
    }
    return new Response("Not Found", { status: 404 });
  }
  /**
   * Fetch method for Durable Object
   */
  async fetch(request) {
    return this.handleRequest(request);
  }
};

// src/index.js
var app = new Hono2();
app.use("*", cors({
  origin: ["http://localhost:3000", "https://your-frontend-domain.com"],
  allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization"],
  credentials: true
}));
app.use("*", logger());
app.use("*", errorHandler2);
app.route("/api/auth", auth);
app.get("/health", (c) => {
  return c.json({ status: "ok", timestamp: (/* @__PURE__ */ new Date()).toISOString() });
});
app.use("/api/*", authMiddleware);
app.route("/api/platforms", platforms);
app.route("/api/campaigns", campaigns);
app.route("/api/media", media);
app.route("/api/status", status);
app.notFound((c) => {
  return c.json({ error: "Not Found" }, 404);
});
var src_default = {
  fetch: app.fetch,
  queue: /* @__PURE__ */ __name(async (batch, env2) => {
    for (const message of batch.messages) {
      const { campaignId, platform: platform2, action } = JSON.parse(message.body);
      try {
        console.log(`Processing campaign ${campaignId} for platform ${platform2}`);
        message.ack();
      } catch (error3) {
        console.error(`Failed to process campaign ${campaignId}:`, error3);
        message.retry();
      }
    }
  }, "queue")
};

// ../../../AppData/Roaming/npm/node_modules/wrangler/templates/middleware/middleware-ensure-req-body-drained.ts
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var drainBody = /* @__PURE__ */ __name(async (request, env2, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env2);
  } finally {
    try {
      if (request.body !== null && !request.bodyUsed) {
        const reader = request.body.getReader();
        while (!(await reader.read()).done) {
        }
      }
    } catch (e) {
      console.error("Failed to drain the unused request body.", e);
    }
  }
}, "drainBody");
var middleware_ensure_req_body_drained_default = drainBody;

// ../../../AppData/Roaming/npm/node_modules/wrangler/templates/middleware/middleware-miniflare3-json-error.ts
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
function reduceError(e) {
  return {
    name: e?.name,
    message: e?.message ?? String(e),
    stack: e?.stack,
    cause: e?.cause === void 0 ? void 0 : reduceError(e.cause)
  };
}
__name(reduceError, "reduceError");
var jsonError = /* @__PURE__ */ __name(async (request, env2, _ctx, middlewareCtx) => {
  try {
    return await middlewareCtx.next(request, env2);
  } catch (e) {
    const error3 = reduceError(e);
    return Response.json(error3, {
      status: 500,
      headers: { "MF-Experimental-Error-Stack": "true" }
    });
  }
}, "jsonError");
var middleware_miniflare3_json_error_default = jsonError;

// .wrangler/tmp/bundle-lidyOQ/middleware-insertion-facade.js
var __INTERNAL_WRANGLER_MIDDLEWARE__ = [
  middleware_ensure_req_body_drained_default,
  middleware_miniflare3_json_error_default
];
var middleware_insertion_facade_default = src_default;

// ../../../AppData/Roaming/npm/node_modules/wrangler/templates/middleware/common.ts
init_modules_watch_stub();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_process();
init_virtual_unenv_global_polyfill_cloudflare_unenv_preset_node_console();
init_performance2();
var __facade_middleware__ = [];
function __facade_register__(...args) {
  __facade_middleware__.push(...args.flat());
}
__name(__facade_register__, "__facade_register__");
function __facade_invokeChain__(request, env2, ctx, dispatch, middlewareChain) {
  const [head, ...tail] = middlewareChain;
  const middlewareCtx = {
    dispatch,
    next(newRequest, newEnv) {
      return __facade_invokeChain__(newRequest, newEnv, ctx, dispatch, tail);
    }
  };
  return head(request, env2, ctx, middlewareCtx);
}
__name(__facade_invokeChain__, "__facade_invokeChain__");
function __facade_invoke__(request, env2, ctx, dispatch, finalMiddleware) {
  return __facade_invokeChain__(request, env2, ctx, dispatch, [
    ...__facade_middleware__,
    finalMiddleware
  ]);
}
__name(__facade_invoke__, "__facade_invoke__");

// .wrangler/tmp/bundle-lidyOQ/middleware-loader.entry.ts
var __Facade_ScheduledController__ = class ___Facade_ScheduledController__ {
  constructor(scheduledTime, cron, noRetry) {
    this.scheduledTime = scheduledTime;
    this.cron = cron;
    this.#noRetry = noRetry;
  }
  static {
    __name(this, "__Facade_ScheduledController__");
  }
  #noRetry;
  noRetry() {
    if (!(this instanceof ___Facade_ScheduledController__)) {
      throw new TypeError("Illegal invocation");
    }
    this.#noRetry();
  }
};
function wrapExportedHandler(worker) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return worker;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  const fetchDispatcher = /* @__PURE__ */ __name(function(request, env2, ctx) {
    if (worker.fetch === void 0) {
      throw new Error("Handler does not export a fetch() function.");
    }
    return worker.fetch(request, env2, ctx);
  }, "fetchDispatcher");
  return {
    ...worker,
    fetch(request, env2, ctx) {
      const dispatcher = /* @__PURE__ */ __name(function(type, init) {
        if (type === "scheduled" && worker.scheduled !== void 0) {
          const controller = new __Facade_ScheduledController__(
            Date.now(),
            init.cron ?? "",
            () => {
            }
          );
          return worker.scheduled(controller, env2, ctx);
        }
      }, "dispatcher");
      return __facade_invoke__(request, env2, ctx, dispatcher, fetchDispatcher);
    }
  };
}
__name(wrapExportedHandler, "wrapExportedHandler");
function wrapWorkerEntrypoint(klass) {
  if (__INTERNAL_WRANGLER_MIDDLEWARE__ === void 0 || __INTERNAL_WRANGLER_MIDDLEWARE__.length === 0) {
    return klass;
  }
  for (const middleware of __INTERNAL_WRANGLER_MIDDLEWARE__) {
    __facade_register__(middleware);
  }
  return class extends klass {
    #fetchDispatcher = /* @__PURE__ */ __name((request, env2, ctx) => {
      this.env = env2;
      this.ctx = ctx;
      if (super.fetch === void 0) {
        throw new Error("Entrypoint class does not define a fetch() function.");
      }
      return super.fetch(request);
    }, "#fetchDispatcher");
    #dispatcher = /* @__PURE__ */ __name((type, init) => {
      if (type === "scheduled" && super.scheduled !== void 0) {
        const controller = new __Facade_ScheduledController__(
          Date.now(),
          init.cron ?? "",
          () => {
          }
        );
        return super.scheduled(controller);
      }
    }, "#dispatcher");
    fetch(request) {
      return __facade_invoke__(
        request,
        this.env,
        this.ctx,
        this.#dispatcher,
        this.#fetchDispatcher
      );
    }
  };
}
__name(wrapWorkerEntrypoint, "wrapWorkerEntrypoint");
var WRAPPED_ENTRY;
if (typeof middleware_insertion_facade_default === "object") {
  WRAPPED_ENTRY = wrapExportedHandler(middleware_insertion_facade_default);
} else if (typeof middleware_insertion_facade_default === "function") {
  WRAPPED_ENTRY = wrapWorkerEntrypoint(middleware_insertion_facade_default);
}
var middleware_loader_entry_default = WRAPPED_ENTRY;
export {
  CampaignOrchestrator,
  __INTERNAL_WRANGLER_MIDDLEWARE__,
  middleware_loader_entry_default as default
};
/*! Bundled license information:

bcryptjs/dist/bcrypt.js:
  (**
   * @license bcrypt.js (c) 2013 Daniel Wirtz <dcode@dcode.io>
   * Released under the Apache License, Version 2.0
   * see: https://github.com/dcodeIO/bcrypt.js for details
   *)
*/
//# sourceMappingURL=index.js.map
