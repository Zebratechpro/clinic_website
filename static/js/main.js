(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealTargets = document.querySelectorAll(
    ".section-kicker, .section-title, .service-card, .gallery-card, .review-card"
  );

  if (!reduceMotion && "IntersectionObserver" in window) {
    document.documentElement.classList.add("reveal-enabled");
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    revealTargets.forEach((target) => {
      target.classList.add("reveal-on-scroll");
      revealObserver.observe(target);
    });
  }

  const menuButton = document.getElementById("menu-button");
  const mobileMenu = document.getElementById("mobile-menu");

  if (menuButton && mobileMenu) {
    menuButton.addEventListener("click", () => {
      const isExpanded = menuButton.getAttribute("aria-expanded") === "true";
      menuButton.setAttribute("aria-expanded", String(!isExpanded));
      mobileMenu.classList.toggle("hidden", isExpanded);
    });

    mobileMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        mobileMenu.classList.add("hidden");
        menuButton.setAttribute("aria-expanded", "false");
      });
    });
  }

  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  const emailPopup = document.getElementById("appointment-email-popup");
  const closeEmailPopup = document.getElementById("close-appointment-email-popup");
  if (emailPopup && closeEmailPopup) {
    const handlePopupKeydown = (event) => {
      if (event.key === "Escape") dismissEmailPopup();
    };
    const dismissEmailPopup = () => {
      emailPopup.classList.add("hidden");
      document.body.classList.remove("overflow-hidden");
      document.removeEventListener("keydown", handlePopupKeydown);
      document.getElementById("submit-button")?.focus();
    };

    document.body.classList.add("overflow-hidden");
    closeEmailPopup.focus();
    closeEmailPopup.addEventListener("click", dismissEmailPopup);
    document.addEventListener("keydown", handlePopupKeydown);
    emailPopup.addEventListener("click", (event) => {
      if (event.target === emailPopup) dismissEmailPopup();
    });
  }

  const form = document.getElementById("booking-form");
  const dateInput = document.getElementById("appointment_date");
  if (dateInput) {
    const localToday = new Date();
    const offset = localToday.getTimezoneOffset();
    const today = new Date(localToday.getTime() - offset * 60_000).toISOString().slice(0, 10);
    dateInput.min = today;
  }

  if (form) {
    form.addEventListener("submit", () => {
      const button = document.getElementById("submit-button");
      if (button && form.checkValidity()) {
        button.disabled = true;
        button.textContent = "Sending request…";
      }
    });
  }
})();
