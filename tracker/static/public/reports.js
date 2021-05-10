const dateLocaleOptions = {
	weekday: "short",
	month: "2-digit",
	day: "numeric",
};
ready(() => {
	let dailyExpenseCtx = document.getElementById("daily-expense-chart");
	dCall("/api/reports", {}, "GET").then((result) => {
		let amounts = result.amounts.map((a) => Math.abs(a));
		let time = result.time.map((t) => new Date(t).toLocaleDateString("en", dateLocaleOptions));
		let maxAmount = Math.max(...amounts);
		let dailyExpenseChart = new Chart(dailyExpenseCtx, {
			type: "bar",
			data: {
				labels: time,
				datasets: [
					{
						label: "Amount spent",
						data: amounts,
					},
				],
			},
			options: {
				scales: {
					yAxes: [
						{
							ticks: {
								suggestedMax: maxAmount + maxAmount * 0.2,
								beginAtZero: true,
							},
						},
					],
				},
				plugins: {
					colorschemes: {
						scheme: "brewer.RdGy3",
					},
				},
			},
		});
	});

	let dailyIncomeCtx = document.getElementById("daily-income-chart");
	dCall("/api/reports?source=income", {}, "GET").then((result) => {
		let amounts = result.amounts.map((a) => Math.abs(a));
		let time = result.time.map((t) => new Date(t).toLocaleDateString("en", dateLocaleOptions));
		let maxAmount = Math.max(...amounts);
		let dailyIncomeChart = new Chart(dailyIncomeCtx, {
			type: "bar",
			data: {
				labels: time,
				datasets: [
					{
						label: "Generated income",
						data: amounts,
					},
				],
			},
			options: {
				scales: {
					yAxes: [
						{
							ticks: {
								suggestedMax: maxAmount + maxAmount * 0.2,
								beginAtZero: true,
							},
						},
					],
				},
				plugins: {
					colorschemes: {
						scheme: "office.GreenYellow6",
					},
				},
			},
		});
	});

	let expenseCtx = document.getElementById("expense-chart");
	dCall("/api/category", {}, "GET").then((result) => {
		console.log(result);
		let expenseChart = new Chart(expenseCtx, {
			type: "pie",
			data: {
				labels: result.titles,
				datasets: [
					{
						label: "Expense by Category",
						data: result.amounts,
						hoverOffset: 4,
					},
				],
			},
			options: {
				plugins: {
					colorschemes: {
						scheme: "brewer.RdBu4",
					},
				},
			},
		});
	});

	let incomeCtx = document.getElementById("income-chart");
	dCall("/api/category?source=income", {}, "GET").then((result) => {
		let incomeChart = new Chart(incomeCtx, {
			type: "pie",
			data: {
				labels: result.titles,
				datasets: [
					{
						label: "Income by Category",
						data: result.amounts,
						hoverOffset: 4,
					},
				],
			},
			options: {
				plugins: {
					colorschemes: {
						scheme: "office.BlueGreen6",
					},
				},
			},
		});
	});
});
