<script>
    import { onMount } from 'svelte';
    import { apihost } from '../../stores.js'
    import {filter, mean} from 'mathjs';

    import Highcharts from 'highcharts';
    import Exporting from 'highcharts/modules/exporting';
    import ExportData from 'highcharts/modules/export-data';

    const today = new Intl.DateTimeFormat('en-CA').format(new Date());

    export let data;
    var allPresses = [];
    var qotd = [];
    var filteredPresses = [];
    var kiosks = [];

    var selectedKiosk;

    var date = new Date();
    let selectedDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toJSON().slice(0, 10);
    let minDate = "";
    let maxDate = "";

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
        var date = new Date();
        var start = new Date(new Date(selectedDate).getTime() + (date.getTimezoneOffset() * 60000)).toJSON();
        var end = new Date(new Date(selectedDate).getTime() + (date.getTimezoneOffset() * 60000) + 24*60*60*1000).toJSON();
        console.log("start: " + start);
        console.log("end: " + end);
        const p = await fetch( $apihost + '/api/button_press/filter',
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    kiosk_id: 666,
                    startdate: start,
                    enddate: end
                })
            });
        return await p.json();
    }

    async function getQotd() {
        const p = await fetch( $apihost + '/api/kiosk/qotd/' + today,
            {
                method: "GET"
            });
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
                text: 'Total ' + ' - ' + selectedDate,
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
                text: 'Hourly ' + ' - ' + selectedDate,
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

        updateCharts(filteredPresses);
    }

    onMount(async () => {
        //qotd = await getQotd();
        qotd = await (await fetch($apihost + "/api/kiosk/qotd/" + today)).json();

        // enable exporting highcharts module
        Exporting(Highcharts);
        ExportData(Highcharts);
        // highcharts set global options
        Highcharts.setOptions({
            time: { timezoneOffset: new Date().getTimezoneOffset() }
        });

        allPresses = await buttonPresses();
        kiosks = await (await fetch($apihost + "/api/kiosk/list")).json();
        console.log("all kiosks: " + kiosks);
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
            refreshData();
        }
    }
</script>


<svelte:head>
    <title>QotD</title>
    <meta name="description" content="About this app" />
</svelte:head>

<section>

    <h1>Question of the Day - {today}</h1>

    <h2>{qotd}</h2>

    <div class="container" style="padding: 0px;">
        <div class="chart" id="hourly-column-container"></div>
        <div class="chart" id="column-container"></div>
    </div>
</section>

<style>
    .chart {
        margin: 0px;
    }
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
    h2 {
        font-size: 1.5em;
        margin-top: 0.5em;
        margin-bottom: 1.5em;
    }
</style>