/** @jsx createElement */
/*** @jsxFrag createFragment */
const { fadeIn, notify, ready, djangoCall, createElement, appendChild, createFragment } = vanjs;
const updateBalance = () => {
	djangoCall("/api/balance", {}, "GET").then((data) => {
		if (!data.error) {
			let balanceValueElm = document.querySelector("#balance-value");
			balanceValueElm.textContent = `$${data.balance}`;
			balanceValueElm.classList.add("animate__animated", "animate__fadeIn");
			balanceValueElm.addEventListener("animationend", () => balanceValueElm.classList.remove("animate__animated", "animate__fadeIn"));
		} else notify(data.error, "danger");
	});
};

const bindRevemoveTransactions = (elms) => {
	elms.forEach((elm) => {
		elm.addEventListener("click", (evt) => {
			let transactionID = evt.target.dataset.transactionId;
			if (confirm("Are you sure to remove ?")) {
				djangoCall("/api/transaction", { transaction_id: transactionID }, "DELETE").then((data) => {
					if (!data.error) {
						let transactionElm = document.querySelector(`#transaction-${transactionID}`);
						let expenseValueElm = document.querySelector("#expense-value");
						let incomeValueElm = document.querySelector("#income-value");
						/*
						 ** As the transactions.js would be used across pages, so there is a mechnism to check if it should update balance on index page as it should.
						 ** The solution is to test if div IDs on index page available or not.
						 */
						if (expenseValueElm && incomeValueElm) {
							let transactionValueElm = document.querySelector(`#transaction-${transactionID} .transaction-value`);
							let transactionValue = parseFloat(transactionValueElm.textContent.replace("$", "").trim());
							if (transactionValue > 0) {
								incomeValueElm.textContent = `$${parseFloat(incomeValueElm.textContent.replace("$", "").trim()) - transactionValue}`;
								fadeIn(incomeValueElm);
							} else if (transactionValue < 0) {
								expenseValueElm.textContent = `$${parseFloat(expenseValueElm.textContent.replace("$", "").trim()) - transactionValue}`;
								fadeIn(incomeValueElm);
							}
							updateBalance();
						}
						transactionElm.classList.add("animate__animated", "animate__fadeOut");
						transactionElm.addEventListener("animationend", () => transactionElm.remove());
						notify(data.message);
					} else notify(data.error, "danger");
				});
			}
		});
	});
};

let isFetching = false;
let nextPage = 2;
const loadMoreTransactions = (page) => {
	isFetching = true;
	djangoCall(`/api/transactions?page=${page}`, {}, "GET").then((data) => {
		if (!data.error) {
			const UsingFragment = (
				<div>
					{data.map((t) => (
						<div id={`transaction-${t.id}`} class={`bg-white p-0 my-1 p-1 ${t.source == "income" ? "transaction-income" : "transaction-expense"}`}>
							<div class='d-flex'>
								<div class='p-1 w-75 bd-highlight'>{t.text}</div>
								<div class='transaction-value p-1 flex-shrink-0'>$ {t.amount}</div>
								<div class='p-1 flex-shrink-1'>
									<i data-transaction-id={t.id} class='btn-icon remove-transaction bi bi-trash'></i>
								</div>
							</div>
							<div class='text-muted pl-1'>
								{t.category_id ? (
									<>
										{t.human_time} in <a href={`category/${t.category_id}`}>{t.category_title}</a>
									</>
								) : (
									<>{t.human_time}</>
								)}
							</div>
						</div>
					))}
				</div>
			);
			document.querySelector("#transactions").appendChild(UsingFragment);
		} else {
			// notify(data.error, "danger");
			let elmMore = document.querySelector("#more");
			elmMore && elmMore.remove();
			document.querySelector("#more-container").textContent = "The End !";
		}
		nextPage++;
		isFetching = false;
	});
};

ready(() => {
	bindRevemoveTransactions(document.querySelectorAll(".remove-transaction"));
	let moreElm = document.querySelector("#more");
	if (moreElm) {
		moreElm.addEventListener("click", () => loadMoreTransactions(nextPage));
		window.onscroll = () => {
			window.innerHeight + window.scrollY >= document.body.offsetHeight &&
				document.querySelector("#more-container").textContent != "The End !" &&
				!isFetching &&
				loadMoreTransactions(nextPage);
		};
	}
});
