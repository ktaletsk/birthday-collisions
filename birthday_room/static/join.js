const body = document.body;
const room = body.dataset.room;
const form = document.querySelector("#birthday-form");
const monthSelect = document.querySelector("#month");
const daySelect = document.querySelector("#day");
const displayNameInput = document.querySelector("#display-name");
const submitButton = form.querySelector("button[type='submit']");
const status = document.querySelector("#status");

const storageKey = `marimo-live-voting:${room}`;
const visitorKey = "marimo-live-voting:visitor-id";

function visitorId() {
  let value = localStorage.getItem(visitorKey);
  if (!value) {
    value =
      globalThis.crypto?.randomUUID?.() ??
      `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(visitorKey, value);
  }
  return value;
}

function populateDays(selectedDay = "") {
  const month = Number(monthSelect.value);
  daySelect.replaceChildren(new Option("Choose day", ""));
  daySelect.disabled = !month;
  if (!month) return;

  const daysInMonth = new Date(2000, month, 0).getDate();
  for (let day = 1; day <= daysInMonth; day += 1) {
    daySelect.add(new Option(String(day), String(day)));
  }
  if (selectedDay && Number(selectedDay) <= daysInMonth) {
    daySelect.value = String(selectedDay);
  }
}

function showStatus(message, kind = "") {
  status.textContent = message;
  status.className = `status ${kind}`.trim();
}

monthSelect.addEventListener("change", () => populateDays());

const saved = JSON.parse(localStorage.getItem(storageKey) ?? "null");
if (saved) {
  displayNameInput.value = saved.displayName ?? "";
  monthSelect.value = String(saved.month);
  populateDays(saved.day);
  showStatus("Your previous answer is loaded. You can change it.", "success");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const month = Number(monthSelect.value);
  const day = Number(daySelect.value);
  const displayName = displayNameInput.value.trim();
  if (!month || !day) return;

  submitButton.disabled = true;
  showStatus("Sending your birthday…");

  try {
    const response = await fetch(
      `/api/rooms/${encodeURIComponent(room)}/birthday`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visitor_id: visitorId(),
          month,
          day,
          display_name: displayName || null,
        }),
      },
    );

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail ?? "The birthday machine objected.");
    }

    localStorage.setItem(
      storageKey,
      JSON.stringify({ displayName, month, day }),
    );
    const count = payload.your_birthday_count;
    const greeting = displayName ? `, ${displayName}` : "";
    const message =
      count > 1
        ? `Saved${greeting}! ${count - 1} other ${count === 2 ? "person has" : "people have"} your birthday.`
        : `Saved${greeting}! So far, your birthday is gloriously unique.`;
    showStatus(message, "success");
    submitButton.textContent = "Update my birthday";
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
});
