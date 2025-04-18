import { createApp, ref } from "vue";
import emitter from "mitt";
import WebSerial from "./WebSerial.js";

globalThis.webSerialManager = new WebSerial();
globalThis.emitter = emitter();

const app = createApp({
  setup: function () {
    const ConsoleLog = ref("");
    const SentLog = ref("");
    const ReceivedLog = ref("");
    const wasConnected = ref(false);
    const clickStart = async function () {
      wasConnected.value = await globalThis.webSerialManager.start();
    };
    const clickClose = async function () {
      wasConnected.value = !(await globalThis.webSerialManager.close());
    };
    const clickTest = async function () {
      await globalThis.webSerialManager.writeSerial("\r\n");
      await globalThis.webSerialManager.waitForPrompt();

      await globalThis.webSerialManager.writeSerial("import sys\r\n");
      await globalThis.webSerialManager.waitForPrompt();

      await globalThis.webSerialManager.writeSerial("print(sys.version)\r\n");
    };
    return {
      ConsoleLog,
      SentLog,
      ReceivedLog,
      wasConnected,
      clickStart,
      clickClose,
      clickTest,
    };
  },
  mounted: function () {
    globalThis.emitter.on("web_serial_console", (logs) => {
      this.ConsoleLog = logs.join("");
    });
    globalThis.emitter.on("web_serial_sent", (logs) => {
      this.SentLog = logs.join("");
    });
    globalThis.emitter.on("web_serial_received", (logs) => {
      this.ReceivedLog = logs.join("");
    });

    globalThis.webSerialManager.setLogConsoleCallback = function (logs) {
      globalThis.emitter.emit("web_serial_console", logs);
    };
    globalThis.webSerialManager.setLogSendCallBack = function (logs) {
      globalThis.emitter.emit("web_serial_sent", logs);
    };
    globalThis.webSerialManager.setLogReceivedCallBack = function (logs) {
      globalThis.emitter.emit("web_serial_received", logs);
    };
  },
});

export default app;
