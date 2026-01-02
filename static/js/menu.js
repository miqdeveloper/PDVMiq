document.addEventListener("DOMContentLoaded", () => {
  
  const menuToggle = document.getElementById("menuToggle");
  const menuDropdown = document.getElementById("menuDropdown");
  const iconMenu = document.getElementById("iconMenu");
  const iconClose = document.getElementById("iconClose");
  
  let isOpen = false;

  menuToggle.addEventListener("click", () => {
    isOpen = !isOpen;

    if (isOpen) {
      menuDropdown.classList.remove("hidden");
      iconMenu.classList.add("hidden");
      iconClose.classList.remove("hidden");

      menuToggle.classList.add(
        "bg-[#0a1e4a]",
        "rotate-90",
        "border",
        "border-white/10"
      );
      menuToggle.classList.remove("bg-gradient-to-r");
    } else {
      menuDropdown.classList.add("hidden");
      iconMenu.classList.remove("hidden");
      iconClose.classList.add("hidden");

      menuToggle.classList.remove(
        "bg-[#0a1e4a]",
        "rotate-90",
        "border",
        "border-white/10"
      );
      menuToggle.classList.add("bg-gradient-to-r");
    }
  });
});
