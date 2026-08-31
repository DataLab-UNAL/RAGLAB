const tabGroups = document.querySelectorAll("[data-tabs]");

tabGroups.forEach((group) => {
  const buttons = group.querySelectorAll("[data-tab-target]");
  const panels = group.querySelectorAll("[data-tab-panel]");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.dataset.tabTarget;

      buttons.forEach((item) => item.classList.remove("active"));
      panels.forEach((panel) => panel.classList.remove("active"));

      button.classList.add("active");
      group.querySelector(`[data-tab-panel="${target}"]`)?.classList.add("active");
    });
  });
});

const copyButtons = document.querySelectorAll("[data-copy]");

copyButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const code = button.closest(".command-block")?.querySelector("code");
    if (!code) {
      return;
    }

    await navigator.clipboard.writeText(code.innerText);
    const previousLabel = button.textContent;
    button.textContent = "Copiado";
    button.classList.add("copied");

    window.setTimeout(() => {
      button.textContent = previousLabel;
      button.classList.remove("copied");
    }, 1200);
  });
});

const mobileNavToggle = document.querySelector(".mobile-nav-toggle");
const sidebar = document.querySelector(".sidebar");
const sideNavLinks = document.querySelectorAll(".side-nav a");

if (mobileNavToggle && sidebar) {
  mobileNavToggle.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("nav-open");
    mobileNavToggle.setAttribute("aria-expanded", String(isOpen));
  });

  sideNavLinks.forEach((link) => {
    link.addEventListener("click", () => {
      document.body.classList.remove("nav-open");
      mobileNavToggle.setAttribute("aria-expanded", "false");
    });
  });
}
