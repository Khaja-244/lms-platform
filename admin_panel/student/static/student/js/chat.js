"use strict";
(() => {
  let roomId = null, socket = null, roomData = [], typingTimer = null;
  const me = LMS.getStoredUser();
  const rooms = document.getElementById("roomList");
  const messages = document.getElementById("messageList");
  const title = document.getElementById("roomTitle");
  const presence = document.getElementById("presenceState");
  const typing = document.getElementById("typingState");
  const input = document.getElementById("messageInput");
  const messageForm = document.getElementById("messageForm");
  const fileInput = document.getElementById("chatFile");
  const fileForm = document.getElementById("fileForm");
  const alertBox = document.getElementById("chatAlert");
  const participantSelect = document.getElementById("participantSelect");
  const esc = value => {
    const node = document.createElement("div");
    node.textContent = value ?? "";
    return node.innerHTML;
  };
  const showError = text => {
    alertBox.textContent = text;
    alertBox.className = "alert alert-danger";
  };
  const otherPeople = room => (room.participants || []).filter(user => Number(user.id) !== Number(me.id));
  const timeText = value => value ? new Date(value).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}) : "";
  function receiptHtml(item) {
    if (Number(item.sender_id) !== Number(me.id)) return "";
    const ticks = item.delivery_status === "sent" ? "✓" : "✓✓";
    const colour = item.delivery_status === "read" ? "#53bdeb" : "currentColor";
    return '<span class="ms-1" data-receipt="' + item.id + '" title="' + esc(item.delivery_status) + '" style="color:' + colour + '">' + ticks + "</span>";
  }
  function renderMessage(item) {
    if (document.querySelector('[data-message-id="' + item.id + '"]')) return;
    const mine = Number(item.sender_id) === Number(me.id);
    const file = item.file_url ? '<a class="d-block fw-semibold" style="color:#08766c" href="' + encodeURI(LMS.apiBaseUrl + item.file_url) + '" target="_blank" rel="noopener noreferrer"><i class="bi bi-paperclip"></i> ' + esc(item.file_name || "Attachment") + "</a>" : "";
    const text = item.message && item.message !== item.file_name ? "<div>" + esc(item.message) + "</div>" : "";
    messages.insertAdjacentHTML("beforeend",
      '<div class="d-flex mb-2 ' + (mine ? "justify-content-end" : "") + '" data-message-id="' + item.id + '">' +
      '<div class="p-2 rounded-3 ' + (mine ? "text-dark" : "bg-light") + '" style="max-width:80%;' + (mine ? "background:#dcf8c6;border:1px solid #c7eab0" : "") + '">' +
      (mine ? "" : '<small class="d-block fw-semibold opacity-75">' + esc(item.sender_name) + "</small>") +
      text + file + '<small class="d-flex justify-content-end align-items-center opacity-75 mt-1">' +
      timeText(item.created_at) + receiptHtml(item) + "</small></div></div>");
    messages.scrollTop = messages.scrollHeight;
  }
  function updateReceipt(ids, status) {
    (ids || []).forEach(id => {
      const node = document.querySelector('[data-receipt="' + id + '"]');
      if (!node) return;
      node.title = status;
      node.textContent = status === "sent" ? "✓" : "✓✓";
      node.style.color = status === "read" ? "#53bdeb" : "currentColor";
    });
  }
  function updatePresence(room) {
    const people = otherPeople(room);
    const online = people.filter(user => user.online);
    if (!people.length) return presence.textContent = "";
    if (room.room_type === "group") {
      presence.textContent = online.length ? online.length + " participant(s) online" : people.length + " participants";
    } else {
      presence.textContent = online.length ? "online" : (people[0].last_seen ? "last seen " + new Date(people[0].last_seen).toLocaleString() : "offline");
      presence.className = "small " + (online.length ? "text-success" : "text-muted");
    }
  }
  function renderRooms() {
    rooms.innerHTML = roomData.length ? roomData.map(room => {
      const online = otherPeople(room).some(user => user.online);
      return '<button class="list-group-item list-group-item-action room-button py-3" data-id="' + room.id + '">' +
        '<div class="d-flex justify-content-between gap-2"><span class="fw-semibold"><span class="me-2 ' +
        (online ? "text-success" : "text-secondary") + '">●</span>' + esc(room.display_name) + "</span>" +
        (room.unread_count ? '<span class="badge rounded-pill text-bg-primary">' + room.unread_count + "</span>" : "") +
        '</div><small class="d-block text-muted text-truncate ms-4">' + esc(room.last_message || (online ? "online" : "No messages yet")) + "</small></button>";
    }).join("") : '<div class="p-3 text-muted">No conversations yet.</div>';
    document.querySelectorAll(".room-button").forEach(button => button.addEventListener("click", () => openRoom(Number(button.dataset.id))));
  }
  async function loadRooms() {
    try {
      roomData = await LMS.get("/chat/rooms");
      renderRooms();
    } catch (error) { showError(error.message); }
  }
  async function loadContacts() {
    try {
      const contacts = await LMS.get("/chat/contacts");
      participantSelect.innerHTML = contacts.map(user => '<option value="' + user.id + '">' + esc(user.name) + " — " + esc(user.role) + "</option>").join("");
    } catch (error) { showError(error.message); }
  }
  async function markRead() {
    if (!roomId) return;
    try {
      await LMS.post("/chat/rooms/" + roomId + "/read", {});
      const room = roomData.find(item => item.id === roomId);
      if (room) room.unread_count = 0;
      renderRooms();
    } catch (_) {}
  }
  async function openRoom(id) {
    roomId = Number(id);
    const room = roomData.find(item => item.id === roomId) || await LMS.get("/chat/rooms/" + roomId);
    title.textContent = room.display_name;
    updatePresence(room);
    messages.innerHTML = "";
    try {
      const page = await LMS.get("/chat/rooms/" + roomId + "/messages");
      page.messages.forEach(renderMessage);
      await markRead();
      connect();
      input.disabled = false;
      messageForm.querySelector("button").disabled = false;
      fileInput.disabled = false;
      fileForm.querySelector("button").disabled = false;
    } catch (error) { showError(error.message); }
  }
  function connect() {
    socket?.close();
    const api = new URL(LMS.apiBaseUrl);
    socket = new WebSocket((api.protocol === "https:" ? "wss:" : "ws:") + "//" + api.host + "/ws/chat/" + roomId + "?token=" + encodeURIComponent(LMS.getAccessToken()));
    socket.onmessage = async event => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === "message") {
          if (Number(data.room_id) === roomId) {
            renderMessage(data);
            if (Number(data.sender_id) !== Number(me.id)) {
              socket.send(JSON.stringify({event: "delivered", message_id: data.id}));
              if (!document.hidden) socket.send(JSON.stringify({event: "read", message_id: data.id}));
            }
          }
          await loadRooms();
        } else if (data.event === "delivered" || data.event === "read") {
          updateReceipt(data.message_ids, data.event);
        } else if (data.event === "typing_start" && Number(data.user_id) !== Number(me.id)) {
          typing.textContent = (data.user_name || "Someone") + " is typing…";
        } else if (data.event === "typing_stop") {
          typing.textContent = "";
        } else if (data.event === "presence") {
          roomData.forEach(room => (room.participants || []).forEach(user => {
            if (Number(user.id) === Number(data.user_id)) {
              user.online = Boolean(data.online);
              user.last_seen = data.last_seen;
            }
          }));
          const active = roomData.find(item => item.id === roomId);
          if (active) updatePresence(active);
          renderRooms();
        }
      } catch (_) {}
    };
  }
  input.addEventListener("input", () => {
    if (socket?.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({event: "typing_start", user_name: me.name}));
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => socket?.readyState === WebSocket.OPEN && socket.send(JSON.stringify({event: "typing_stop"})), 900);
  });
  messageForm.addEventListener("submit", async event => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || !roomId) return;
    try {
      if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({event: "message", message: text, message_type: "text"}));
      else renderMessage(await LMS.post("/chat/messages", {room_id: roomId, message: text, message_type: "text"}));
      input.value = "";
      if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({event: "typing_stop"}));
    } catch (error) { showError(error.message); }
  });
  fileForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (!fileInput.files[0] || !roomId) return;
    const data = new FormData();
    data.append("file", fileInput.files[0]);
    try {
      await LMS.request("/chat/upload/" + roomId, {method: "POST", body: data});
      fileInput.value = "";
    } catch (error) { showError(error.message); }
  });
  document.getElementById("newRoomForm").addEventListener("submit", async event => {
    event.preventDefault();
    const data = new FormData(event.target);
    const ids = [...participantSelect.selectedOptions].map(option => Number(option.value));
    const type = String(data.get("room_type"));
    if (type === "private" && ids.length !== 1) return showError("Choose exactly one instructor for a private conversation.");
    if (type === "group" && (!data.get("name") || !ids.length)) return showError("Enter a group name and choose at least one participant.");
    try {
      const room = await LMS.post("/chat/rooms", {name: type === "group" ? data.get("name") : null, room_type: type, participant_ids: ids});
      bootstrap.Modal.getInstance(document.getElementById("newRoomModal")).hide();
      event.target.reset();
      await loadRooms();
      await openRoom(room.id);
    } catch (error) { showError(error.message); }
  });
  document.addEventListener("visibilitychange", () => !document.hidden && markRead());
  window.addEventListener("beforeunload", () => socket?.close());
  Promise.all([loadRooms(), loadContacts()]);
})();
