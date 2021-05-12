const { fadeIn, ready, djangoCall, createElement, appendChild, createFragment } = vanjs;

ready(() => {
	// Handle closing button for messages
	document.querySelectorAll(".btn-close").forEach((btn) => {
		btn.addEventListener("click", () => {
			btn.parentElement.classList.add("animate__animated", "animate__fadeOut");
			btn.parentElement.addEventListener("animationend", () => btn.parentElement.remove());
		});
	});
});
