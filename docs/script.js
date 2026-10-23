const tabGroups = document.querySelectorAll("[data-tabs]");

const courseTabs = [...document.querySelectorAll('#course-nav [role="tab"]')];
const navDisclosure = document.querySelector(".nav-disclosure");
const coursePanels = courseTabs
  .map((tab) => document.getElementById(tab.getAttribute("aria-controls")))
  .filter(Boolean);

function selectCourseTab(tab, updateUrl = true) {
  const panelId = tab.getAttribute("aria-controls");

  courseTabs.forEach((item) => {
    const selected = item === tab;
    item.setAttribute("aria-selected", String(selected));
    item.tabIndex = selected ? 0 : -1;
  });

  coursePanels.forEach((panel) => {
    const selected = panel.id === panelId;
    const panelTab = courseTabs.find((item) => item.getAttribute("aria-controls") === panel.id);
    panel.hidden = !selected;
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", panelTab.id);
    panel.tabIndex = 0;
  });

  if (updateUrl) {
    history.replaceState(null, "", `#${panelId}`);
    if (window.matchMedia("(max-width: 960px)").matches && navDisclosure) {
      navDisclosure.open = false;
    }
  }
}

if (courseTabs.length) {
  if (window.matchMedia("(max-width: 960px)").matches && navDisclosure) {
    navDisclosure.open = false;
  }

  courseTabs.forEach((tab, index) => {
    tab.id ||= `tab-${tab.getAttribute("aria-controls")}`;
    tab.addEventListener("click", (event) => {
      event.preventDefault();
      selectCourseTab(tab);
    });

    tab.addEventListener("keydown", (event) => {
      const direction = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      if (!direction) return;
      event.preventDefault();
      const next = courseTabs[(index + direction + courseTabs.length) % courseTabs.length];
      next.focus();
      selectCourseTab(next);
    });
  });

  const initialTab = courseTabs.find((tab) => tab.getAttribute("href") === window.location.hash)
    || courseTabs[0];
  selectCourseTab(initialTab, false);

  window.addEventListener("hashchange", () => {
    const matchingTab = courseTabs.find((tab) => tab.getAttribute("href") === window.location.hash);
    if (matchingTab) selectCourseTab(matchingTab, false);
  });
}

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
    const copyScope = button.closest("[data-copy-scope]");
    const copyTarget = copyScope?.querySelector("pre")
      || copyScope?.querySelector("code")
      || button.closest(".command-block")?.querySelector("pre, code");
    if (!copyTarget) {
      return;
    }

    await navigator.clipboard.writeText(copyTarget.innerText);
    const previousLabel = button.textContent;
    button.textContent = "Copiado";
    button.classList.add("copied");

    window.setTimeout(() => {
      button.textContent = previousLabel;
      button.classList.remove("copied");
    }, 1200);
  });
});

const gitWorkflowDialog = document.querySelector("#git-workflow-dialog");
const openGitVisualButton = document.querySelector("[data-open-git-visual]");
const closeGitVisualButton = document.querySelector("[data-close-git-visual]");

if (gitWorkflowDialog && openGitVisualButton) {
  openGitVisualButton.addEventListener("click", () => gitWorkflowDialog.showModal());
  closeGitVisualButton?.addEventListener("click", () => gitWorkflowDialog.close());
  gitWorkflowDialog.addEventListener("click", (event) => {
    if (event.target === gitWorkflowDialog) gitWorkflowDialog.close();
  });
}

const courseImageDialog = document.querySelector("#course-image-dialog");
const courseImagePreview = document.querySelector("[data-course-image-preview]");
const courseImageCaption = document.querySelector("[data-course-image-caption]");

if (courseImageDialog && courseImagePreview && courseImageCaption) {
  document.querySelectorAll("[data-open-course-image]").forEach((button) => {
    button.addEventListener("click", () => {
      const image = button.querySelector("img");
      const caption = button.closest("figure")?.querySelector("figcaption");
      if (!image) return;

      courseImagePreview.src = image.src;
      courseImagePreview.alt = image.alt;
      courseImageCaption.textContent = caption?.innerText || image.alt;
      courseImageDialog.showModal();
    });
  });

  document.querySelector("[data-close-course-image]")?.addEventListener("click", () => courseImageDialog.close());
  courseImageDialog.addEventListener("click", (event) => {
    if (event.target === courseImageDialog) courseImageDialog.close();
  });
}
