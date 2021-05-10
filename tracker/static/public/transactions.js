/** @jsx createElement */
/*** @jsxFrag createFragment */

const createElement = (tag, props, ...children) => {
	if (typeof tag === "function") return tag(props, ...children);
	const element = document.createElement(tag);

	Object.entries(props || {}).forEach(([name, value]) => {
		if (name.startsWith("on") && name.toLowerCase() in window) element.addEventListener(name.toLowerCase().substr(2), value);
		else element.setAttribute(name, value.toString());
	});

	children.forEach((child) => {
		appendChild(element, child);
	});

	return element;
};

const appendChild = (parent, child) => {
	if (Array.isArray(child)) child.forEach((nestedChild) => appendChild(parent, nestedChild));
	else parent.appendChild(child.nodeType ? child : document.createTextNode(child));
};

const createFragment = (props, ...children) => {
	return children;
};

const updateBalance = () => {
	dCall("/api/balance", {}, "GET").then((data) => {
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
				dCall("/api/transaction", { transaction_id: transactionID }, (method = "DELETE")).then((data) => {
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
								incomeValueElm.classList.add("animate__animated", "animate__fadeIn");
								incomeValueElm.addEventListener("animationend", () => incomeValueElm.classList.remove("animate__animated", "animate__fadeIn"));
							} else if (transactionValue < 0) {
								expenseValueElm.textContent = `$${parseFloat(expenseValueElm.textContent.replace("$", "").trim()) - transactionValue}`;
								expenseValueElm.classList.add("animate__animated", "animate__fadeIn");
								expenseValueElm.addEventListener("animationend", () => expenseValueElm.classList.remove("animate__animated", "animate__fadeIn"));
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

const loadMoreTransactions = (page) => {
	dCall(`/api/transactions?page=${page}`, {}, "GET").then((data) => {
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
			nextPage++;
		} else {
			notify(data.error, "danger");
			document.querySelector("#more").remove();
			document.querySelector("#more-container").textContent = "The End !";
		}
	});
};
let nextPage = 2;
ready(() => {
	bindRevemoveTransactions(document.querySelectorAll("i.remove-transaction"));
	document.querySelector("#more").addEventListener("click", (evt) => loadMoreTransactions(nextPage));
});
