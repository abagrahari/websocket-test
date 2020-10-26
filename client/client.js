"use strict";

const N_FLOATS = 2
// assumes float32 data is sent in binary

let mainSocket = new WebSocket("ws://localhost:8080/ws");
mainSocket.binaryType = 'arraybuffer'
let firstTime = true;

function send_json() {
  let name = "create";
  let kwargs = { n: N_FLOATS };
  const payload = JSON.stringify([name, kwargs]);
  mainSocket.send(payload);
}

function send_binary() {
  const arrSize = N_FLOATS;
  const buffer = new ArrayBuffer(4 * arrSize); // 8 Bytes
  const arr = new Float32Array(buffer); // each entry is 4 bytes each
  for (var i = 0; i < arr.length; i++) {
    arr[i] = Math.random() * 10;
  }
  mainSocket.send(arr);
  console.log("Sending:", arr);
}

function disconnect() {
  mainSocket.close();
}

mainSocket.onopen = function (e) {
  send_json();
};


mainSocket.onmessage = function (event) {
  if (isBinary(event.data)) {
    const arr = new Float32Array(event.data);
    console.log("Received:", arr);
    send_binary();
  }
  else if (isString(event.data)) {
    const json = JSON.parse(event.data);
    const event_name = json[0]
    const kwargs = json[1]
    if (event_name == "created") {
      if (firstTime) {
        firstTime = false;
        send_binary();
        send_json();
      } else {
        send_json();
      }

    }
  }

};

mainSocket.onclose = function (event) {
  console.info("Closed")
};

mainSocket.onerror = function (error) {
  console.warn(`[error] ${error.message}`);
};

function isString(s) {
  return typeof (s) === 'string' || s instanceof String;
}

function isBinary(b) {
  return b instanceof ArrayBuffer;
  // similar to isinstance() in Python
}