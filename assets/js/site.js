// Toggle blocks.
document.querySelectorAll(".notion-toggle__summary").forEach((summary) => {
  summary.addEventListener("click", () => {
    const toggle = summary.parentElement;
    const open = toggle.classList.toggle("open");
    toggle.classList.toggle("closed", !open);
    summary.nextElementSibling.style.display = open ? "" : "none";
  });
});

// Copy buttons on code blocks.
document.querySelectorAll(".notion-code__copy-button").forEach((button) => {
  button.addEventListener("click", () => {
    navigator.clipboard.writeText(button.parentElement.querySelector("code").innerText);
  });
});
