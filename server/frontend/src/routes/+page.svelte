<script>
	import Counter from './Counter.svelte';
	import welcome from '$lib/images/svelte-welcome.webp';
	import welcome_fallback from '$lib/images/svelte-welcome.png';
	import { onMount } from 'svelte';
	import {filter, mean} from 'mathjs';
	import SveltyPicker from 'svelty-picker';

	import Highcharts from 'highcharts';
	import Exporting from 'highcharts/modules/exporting';
	import ExportData from 'highcharts/modules/export-data';

	export let data;
	var allPresses = [];
	var filteredPresses = [];
	var kiosks = [];

	var selectedKiosk;

	var date = new Date();
	let selectedDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toJSON().slice(0, 10);
	let minDate = "";
	let maxDate = "";

	let totalPresses = 0;
	let averageButtonPress = 0;

	let chartExportOptions = {
		buttons: {
			contextButton: {
				menuItems: ["printChart",
					"separator",
					"downloadPNG",
					"downloadJPEG",
					"downloadPDF",
					"downloadSVG",
					"separator",
					"downloadCSV",
					"downloadXLS",
					//"viewData",
					"openInCloud"]
			}
		}
	}

	async function buttonPresses() {
		const p = await fetch('http://bigbutton.cluoma.com/api/button_press');
		return await p.json();
	}

	var groupBy = function(xs, key) {
		return xs.reduce(function(rv, x) {
			(rv[x[key]] = rv[x[key]] || []).push(x);
			return rv;
		}, {});
	};

	async function refreshData() {
		allPresses = await buttonPresses();
		await filterPresses();
	}

	function updateCharts(data) {
		console.log("updating charts");
		var allPressesGrouped = groupBy(data, 'button');
		var buttonPressCounts = Object.keys(allPressesGrouped).map((key) => allPressesGrouped[key].length);
		let colours = ["#33a02c","#ffed1f","#ff7f00","#e31a1c"];

		// Highcharts.chart('container', {
		// 	exporting: chartExportOptions,
		// 	series: [{ data: data.map(x => x.button)}]
		// });
		Highcharts.chart('column-container', {
			chart: {type: 'column'},
			exporting: chartExportOptions,
			credits: { enabled: false },
			title: {
				text: 'Total Button Presses' + ' - ' + selectedDate,
				align: 'left'
			},
			plotOptions: {
				series: {
					colorByPoint: true,
					colors: colours
				}
			},
			legend: {enabled: false},
			xAxis: {categories: Object.keys(allPressesGrouped)},
			yAxis: {
				title: {text: 'Button Presses'}
			},
			series: [{ data: buttonPressCounts}]
		});

		// Hourly column chart
		// turn datetimes into only the hour
		data.map(x => {
			var hourDate = new Date(x.serverdate + "Z");
			hourDate.setMinutes(0, 0, 0);
			x.serverdatehour = hourDate;
		});
		// create df and count instances
		let df = new dfd.DataFrame(data);
		let group_df = df.groupby(["serverdatehour","button"]).count();
		let group_df_mean = df.groupby(["serverdatehour"]).agg({button:"mean"});
		//group_df_mean.print();
		// get unique buttons and add them to the
		let buttons = group_df["button"].unique().sortValues().values;
		let dataSeries = [];
		for (const x of buttons) {
			let group_df1 = group_df.query(group_df["button"].eq(x));
			let combine = group_df1["serverdatehour"].values.map((x) => x.getTime()).map((e, i) => [e, group_df1["id_count"].values[i]]);
			dataSeries.push({ type: 'column', name: x, color: colours[x-1], data: combine });
		}
		let combine2 = group_df_mean["serverdatehour"].values.map((x) => x.getTime()).map((e, i) => [e, group_df_mean["button_mean"].values[i]]);
		dataSeries.push({type: 'spline', name: 'Average', yAxis: 1, data: combine2});

		Highcharts.chart('hourly-column-container', {

			credits: { enabled: false },
			title: {
				text: 'Hourly Button Presses' + ' - ' + selectedDate,
				align: 'left'
			},
			tooltip: {
				shared: true
			},
			xAxis: {
				type: 'datetime',
				labels: {format: '{value:%H:%M}'},
				title: {text: 'Hour'},
				crosshair: false
			},
			yAxis: [
				{ title: {text: 'Button Presses'} },
				{ // Secondary yAxis
					title: {text: 'Average'},
					opposite: true
				}
			],
			plotOptions: {
				column: {
					stacking: 'normal',
				},
				series: {
					stacking: 'normal',
					pointPadding: 0.01,
					groupPadding: 0,
					states: {
						inactive: {
							enabled: false
						}
					}
				}
			},
			exporting: chartExportOptions,
			series: dataSeries
		});
	}
	function filterPresses() {
		// filter the kiosk
		//filteredPresses = JSON.parse(JSON.stringify(allPresses));
		filteredPresses = allPresses.filter(function (el) {
			return el.kiosk_id === selectedKiosk;
		});
		// filter the selected day
		filteredPresses = filteredPresses.filter(function (el) {
			var date = new Date(el.serverdate + "Z");
			date = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toJSON().slice(0, 10);
			//console.log(date + " === " + selectedDate);
			return date === selectedDate;
		});

		// get totals and average
		totalPresses = Object.keys(filteredPresses).length;
		averageButtonPress = filteredPresses.length > 0 ? mean(filteredPresses.map(x => x.button)) : 0;

		updateCharts(filteredPresses);
	}

	onMount(async () => {
		// enable exporting highcharts module
		Exporting(Highcharts);
		ExportData(Highcharts);
		// highcharts set global options
		Highcharts.setOptions({
			time: { timezoneOffset: new Date().getTimezoneOffset() }
		});

		allPresses = await buttonPresses();
		kiosks = [...new Set(allPresses.map(x => x.kiosk_id))];
		selectedKiosk = kiosks[0];
		// buttons = [...new Set(allPresses.map(x => x.button))];
		minDate = new Date(Math.min(...[...new Set(allPresses.map(x => new Date(x.serverdate + "Z")))]));
		minDate = new Date(minDate.getTime() - (minDate.getTimezoneOffset() * 60000)).toJSON().slice(0, 10);
		maxDate = new Date(Math.max(...[...new Set(allPresses.map(x => new Date(x.serverdate + "Z")))]));
		maxDate = new Date(maxDate.getTime() - (maxDate.getTimezoneOffset() * 60000)).toJSON().slice(0, 10);
		console.log(minDate);
		console.log(maxDate);

		filterPresses();

		// var df = new dfd.DataFrame(allPresses);
		// df.print();
	});

	function swapDate(e) {
		console.log(e.detail)
		console.log(selectedDate)
		if (e.detail !== selectedDate) {
			selectedDate = e.detail;
			filterPresses();
		}
	}
</script>

<svelte:head>
	<title>Home</title>
	<meta name="description" content="Svelte demo app" />
</svelte:head>

<section>
	<h1>
		Daily Tracking
	</h1>

	<div class="container">

		<div class="selector">
			<h4></h4>
			<button class="button" on:click={refreshData}>Refresh</button>
		</div>

		<div class="selector">
		<h4>Choose a kiosk:</h4>
		<select bind:value={selectedKiosk} on:change={filterPresses} name="kiosks" id="kiosk-select">
		<option value="">--select a kiosk--</option>
		{#each kiosks as k}
			<option value="{k}">{k}</option>
		{/each}
		</select>
		</div>

<!--	<label for="start">Start date:</label>-->
<!--	<input type="date" value={selectedDate} on:input={e => {selectedDate = e.target.value || selectedDate; filterPresses();}} id="start" name="trip-start" min="{minDate}" max="{maxDate}" />-->
		<div class="selector">
			<h4>Choose a Day:</h4>
			<SveltyPicker value={selectedDate}
						  startDate={minDate}
						  endDate={maxDate}
						  mode="date" displayFormat="yyyy-mm-dd"
						  on:change={swapDate}/>
		</div>

	</div>

	<div class="container">
		<div class="selector">
		<h4>Total Presses: </h4>
			<div class="counter"><strong>{totalPresses}</strong></div>
		</div>

		<div class="selector">
			<div><h4>Average Sentiment: </h4></div>
				<div class="counter"><strong>{averageButtonPress.toFixed(2)}</strong></div>
		</div>

	</div>


	<div class="container">
		<div class="chart" id="hourly-column-container"></div>
		<div class="chart" id="column-container"></div>
	</div>
<!--	<div class="charts-row" id="charts">-->
<!--		<div class="chart" id="container"></div>-->
<!--	</div>-->

</section>

<style>
	.container {
		display: flex;
		flex-direction: row;
		width: 100%;
		background-color: #44444411;
		padding-left: 1em;
		padding-right: 1em;
	}
	.chart {
		display: flex;
		width: 50%;
		min-width: 50%;
	}
	.selector {
		width: 20%;
	}
	.button {
		border: none;
		color: white;
		padding: 16px 32px;
		text-align: center;
		text-decoration: none;
		display: inline-block;
		font-size: 16px;
		margin: 4px 2px;
		transition-duration: 0.4s;
		cursor: pointer;
		background-color: #27708d;
		color: white;
		border: 2px solid #27708d;
		justify-content: center;
		align-items: center;
	}
	.button:hover {
		background-color: #008CBA;
		color: white;
	}

	@media screen and (max-width:990px) {
		.container {
			flex-wrap: wrap;
			align-items: center;
			justify-content: center;
		}
		.chart {
			display: flex;
			width: 100%;
			min-width: 100%;
		}
		.selector {
			width: 40%;
		}
	}

	section {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		flex: 0.6;
	}

	h1 {
		width: 100%;
	}

	.welcome {
		display: block;
		position: relative;
		width: 100%;
		height: 0;
		padding: 0 0 calc(100% * 495 / 2048) 0;
	}

	.welcome img {
		position: absolute;
		width: 100%;
		height: 100%;
		top: 0;
		display: block;
	}

	.counter {
		height: 4em;
		text-align: left;
		position: relative;
		margin-top: -1em;
	}

	.counter strong {
		position: absolute;
		display: flex;
		width: 100%;
		height: 100%;
		font-weight: 400;
		color: var(--color-theme-1);
		font-size: 4rem;
		align-items: center;
	}
</style>
