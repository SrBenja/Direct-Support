(() => {
  "use strict";

  const toast = document.getElementById("toast");
  let toastTimer;

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("show"), 1600);
  }

  function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    let copied = false;
    try {
      copied = document.execCommand("copy");
    } catch {
      copied = false;
    }

    textarea.remove();
    return copied;
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch {
        // Fall through to the local fallback.
      }
    }
    return fallbackCopy(text);
  }

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copy);
      if (!target) return;

      const copied = await copyText(target.textContent.trim());
      showToast(copied ? "Copied" : "Unable to copy automatically");
    });
  });

  document.querySelectorAll("[data-copy-group]").forEach((button) => {
    button.addEventListener("click", async () => {
      const groupName = button.dataset.copyGroup;
      const group = document.querySelector(`[data-group="${groupName}"]`);
      if (!group) return;

      const lines = Array.from(group.querySelectorAll("[data-label]")).map((item) => {
        return `${item.dataset.label}: ${item.textContent.trim()}`;
      });

      const copied = await copyText(lines.join("\n"));
      const label = groupName === "ach" ? "ACH" : "SEPA";
      showToast(copied ? `All ${label} details copied` : "Unable to copy automatically");
    });
  });
})();
