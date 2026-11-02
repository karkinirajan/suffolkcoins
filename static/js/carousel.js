// Rotates the banners of [data-carousel]. It replaces an Alpine.js build loaded from unpkg.
(() => {
  const root = document.querySelector("[data-carousel]");
  if (!root) return;
  const slides = [...root.querySelectorAll("[data-slide]")];
  const index = root.querySelector("[data-carousel-index]");
  const count = root.querySelector("[data-carousel-count]");
  if (count) count.textContent = String(slides.length);
  if (slides.length < 2) return;

  let current = 0;
  const show = (next) => {
    slides[current].classList.add("hidden");
    current = next % slides.length;
    slides[current].classList.remove("hidden");
    if (index) index.textContent = String(current + 1);
  };

  // People who ask their system for less motion get a still banner, which they can step through by clicking.
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduced) setInterval(() => show(current + 1), 3000);
  root.addEventListener("click", (event) => {
    if (event.target.closest("a")) return; // the banners are links
    show(current + 1);
  });
})();
