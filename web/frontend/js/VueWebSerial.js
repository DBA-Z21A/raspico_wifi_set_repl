// vueWebSerial.js
import { ref, onMounted } from "vue";
import emitter from "mitt";
import WebSerial from "./WebSerial.js";

globalThis.webSerialManager = new WebSerial();
globalThis.emitter = emitter();

export function vueWebSerial() {
  const ConsoleLog = ref("");
  const SentLog = ref("");
  const ReceivedLog = ref("");
  const wasConnected = ref(false);

  const clickStart = async () => {
    wasConnected.value = await globalThis.webSerialManager.start();
  };
  const clickClose = async () => {
    wasConnected.value = !(await globalThis.webSerialManager.close());
  };
  const clickTest = async () => {
    await globalThis.webSerialManager.writeSerial("\r\n");
    await globalThis.webSerialManager.waitForPrompt();

    await globalThis.webSerialManager.writeSerial("import sys\r\n");
    await globalThis.webSerialManager.waitForPrompt();

    await globalThis.webSerialManager.writeSerial("print(sys.version)\r\n");
  };

  onMounted(() => {
    globalThis.emitter.on("web_serial_console", (logs) => {
      ConsoleLog.value = logs.join("");
    });
    globalThis.emitter.on("web_serial_sent", (logs) => {
      SentLog.value = logs.join("");
    });
    globalThis.emitter.on("web_serial_received", (logs) => {
      ReceivedLog.value = logs.join("");
    });

    globalThis.webSerialManager.setLogConsoleCallback = (logs) => {
      globalThis.emitter.emit("web_serial_console", logs);
    };
    globalThis.webSerialManager.setLogSendCallBack = (logs) => {
      globalThis.emitter.emit("web_serial_sent", logs);
    };
    globalThis.webSerialManager.setLogReceivedCallBack = (logs) => {
      globalThis.emitter.emit("web_serial_received", logs);
    };
  });

  return {
    ConsoleLog,
    SentLog,
    ReceivedLog,
    wasConnected,
    clickStart,
    clickClose,
    clickTest,
  };
}
