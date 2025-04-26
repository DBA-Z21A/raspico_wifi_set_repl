class WebSerial {
  port = null;
  reader = null;
  writer = null;
  prompt = ">>>";
  wasReceivedPrompt = true;
  promptWaitTime = 50;
  promptTimeout = 5000;

  //このクラス自体からのメッセージ
  log_console = [];
  setLogConsoleCallback = null;
  addConsoleLog(message) {
    message = message + "\n";
    this.log_console.push(message);
    console.log("log_console:" + message);
    if (this.setLogConsoleCallback) {
      this.setLogConsoleCallback(this.log_console);
    }
  }

  //送信ログ
  log_send = [];
  setLogSendCallBack = null;
  addSendLog(message) {
    this.log_send.push(message);
    console.log("log_send:" + message);
    if (this.setLogSendCallBack) {
      this.setLogSendCallBack(this.log_send);
    }
  }

  //受信ログ
  log_received = [];
  setLogReceivedCallBack = null;
  addReceivedLog(message) {
    this.log_received.push(message);
    console.log("log_received:" + message);
    if (this.setLogReceivedCallBack) {
      this.setLogReceivedCallBack(this.log_received);
    }
  }

  //WebブラウザがWeb Serial APIに対応しているかを判定
  canUseWebSerialAPI() {
    return window.navigator.serial;
  }

  //処理開始
  async start(portrate = 115200) {
    try {
      //APIが存在する事を確認
      if (!this.canUseWebSerialAPI()) {
        this.addConsoleLog("シリアルポートは使用できません。");
        return false;
      }

      //接続実行
      this.port = await navigator.serial.requestPort();
      if (this.port) {
        await this.port.open({ baudRate: portrate });
        this.reader = this.port.readable.getReader();
        this.writer = this.port.writable.getWriter();
        this.addConsoleLog("シリアルポートに接続しました。");
        this.startReadLoop();
        return true;
      }
    } catch (error) {
      this.addConsoleLog("シリアルポートへの接続に失敗しました: " + error);
    }
    return false;
  }

  //処理終了
  async close() {
    if (this.reader) {
      await this.reader.cancel();
      await this.reader.releaseLock();
      this.reader = null;
    }
    if (this.writer) {
      await this.writer.close();
      await this.writer.releaseLock();
      this.writer = null;
    }
    if (this.port && this.port.readable) {
      await this.port.readable.cancel();
    }
    if (this.port) {
      await this.port.close();
      this.port = null;
    }
    this.addConsoleLog("シリアルポートから切断しました。");
    return true;
  }

  //シリアルポートに対しての送信処理
  async writeSerial(data) {
    if (this.writer) {
      const dataArray = new TextEncoder().encode(data);
      await this.writer.write(dataArray);
      this.addSendLog(data);
      this.wasReceivedPrompt = false;
    }
  }

  //シリアルポートからの受信処理
  async startReadLoop() {
    try {
      while (this.port && this.port.readable && this.reader) {
        const { value, done } = await this.reader.read();
        if (done) {
          this.addConsoleLog("リーダーが閉じられました。");
          break;
        }
        if (value) {
          const textDecoder = new TextDecoder();
          const receivedText = textDecoder.decode(value);
          this.addReceivedLog(receivedText);

          const trimmedValue = receivedText.trimEnd();
          if (trimmedValue.endsWith(this.prompt)) {
            this.wasReceivedPrompt = true;
          }
        }
      }
    } catch (error) {
      if (this.port && this.port.readable) {
        this.addConsoleLog("読み取り中にエラーが発生しました: " + error);
      }
    } finally {
      if (this.reader) {
        this.reader.releaseLock();
      }
    }
  }

  //送信後にこのメソッドをawaitする事により、指定されたプロンプトを受信するまで待機する
  async waitForPrompt() {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const checkPrompt = () => {
        if (this.wasReceivedPrompt) {
          resolve();
        } else if (Date.now() - startTime > this.promptTimeout) {
          reject(new Error("プロンプト受信タイムアウト"));
        } else {
          setTimeout(checkPrompt, this.promptWaitTime);
        }
      };
      checkPrompt();
    });
  }

  //複数コマンドを一括して送信
  async sendCommands(lines) {
    for (const line of lines) {
      await this.writeSerial(line + "\r");
      await this.waitForPrompt();
    }
  }

  //REPLをソフトリブート
  async REPLReset() {
    await this.writeSerial("\x03"); // Ctrl+C
    await this.writeSerial("\x04"); // Ctrl+D（ソフトリブート）
  }
}
export default WebSerial;
