ready(() => {
	let removeCategoryElms = document.querySelectorAll("i.remove-category");
	removeCategoryElms.forEach((elm) => {
		elm.addEventListener("click", (evt) => {
			let categoryID = evt.target.dataset.categoryId;
			if (confirm("Are you sure to remove ?")) {
				dCall("/api/category", { category_id: categoryID }, (method = "DELETE")).then((data) => {
					if (!data.error) {
						let cateogryElm = document.querySelector(`#category-${categoryID}`);
						cateogryElm.classList.add("animate__animated", "animate__fadeOut");
						cateogryElm.addEventListener("animationend", () => cateogryElm.remove());
						notify(data.message);
					} else notify(data.error, "danger");
				});
			}
		});
	});
});
