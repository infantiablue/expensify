ready(() => {
	// let removeTransactionElms = document.querySelectorAll("i.remove-transaction");
	bindRevemoveTransactions(document.querySelectorAll("i.remove-transaction"));
});

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
