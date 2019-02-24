var queryPlotPressure = '&realtime=true'
var queryMarketDepth = '&realtime=true'

function PlotMarketdepth (query, CanvasName) {
  // This function gets the data from the API and draws the MarketDepth plot
  fetch('https://cors-anywhere.herokuapp.com/https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1?type=mdr' + query, {
    method: 'GET',
    mode: 'cors',
    cache: 'no-cache',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => res.json())
    .then(function (data) {
      if (data.orders != null) {
        var BidsDataPoints = []
        var AsksDataPoints = []
        var BidsTotal = 0.0
        var AsksTotal = 0.0
        // Putting data in arrays to be plotted
        for (var i = 0.5; i < 20.0; i += 0.5) {
          if (i.toFixed(2) in data.orders) {
            AsksDataPoints.push({ x: i, y: parseFloat(data.orders[i.toFixed(2)]) / 1000000 })
          }
          if ((-i).toFixed(2) in data.orders) {
            BidsDataPoints.push({ x: -i, y: parseFloat(data.orders[(-i).toFixed(2)]) / 1000000 })
          }
        }
        // Plotting
        var chart = new CanvasJS.Chart(CanvasName, {
          animationEnabled: false,
          title: {
            text: 'Crypto Market Depth'
          },
          axisY: {
            title: 'USD',
            suffix: ' M'
          },
          axisX: {
            title: 'Order price relative to coin price (%)'
          },
          toolTip: {
            shared: true
          },
          data: [{
            type: 'stackedArea',
            showInLegend: true,
            yValueFormatString: "$####### M",
            color: "rgba(255, 0, 0, 1)",
            name: 'Asks',
            dataPoints: AsksDataPoints
          },
          {
            type: 'stackedArea',
            name: 'Bids',
            yValueFormatString: "$####### M",
            color: "rgba(60,179,113, 1)",
            showInLegend: true,
            dataPoints: BidsDataPoints
          }]
        })
        chart.render()
      }
    }
    )
}


function CalculateMDR (BuyPressure, SellPressure) {
  return (100 * (BuyPressure - SellPressure) / (BuyPressure + SellPressure))
}

function PlotPressure (query, CanvasName) {
  // This function gets the data from the API and draws the Buy/Sell Pressure and MDR plots
  fetch('https://cors-anywhere.herokuapp.com/https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1?type=mdr_over_time' + query, {
    method: 'GET',
    mode: 'cors',
    cache: 'no-cache',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => res.json())
    .then(function (data) {
      if (data != null) {
        var BuyPressure = []
        var SellPressure = []
        var MDR = []
        // Putting data in arrays to be plotted
        for (var key in data) {
          var date = key.split(' ')
          BuyPressure.push({ x: new Date(date[0] + 'T' + date[1] + ':00Z'), y: parseFloat(data[key]['Buy Pressure']) / 1000000 })
          SellPressure.push({ x: new Date(date[0] + 'T' + date[1] + ':00Z'), y: parseFloat(data[key]['Sell Pressure']) / 1000000 })
          MDR.push({ x: new Date(date[0] + 'T' + date[1] + ':00Z'),
            y: CalculateMDR(
              parseFloat(data[key]['Buy Pressure']) / 1000000,
              parseFloat(data[key]['Sell Pressure']) / 1000000
            )
          })
        }
        // Plotting
        var chart = new CanvasJS.Chart(CanvasName, {
          animationEnabled: false,
          title: {
            text: 'Buy/Sell Pressure'
          },
          axisX: {
            valueFormatString: 'HH:mm'
          },
          axisY: {
            title: 'USD',
            includeZero: true,
            suffix: ' M'
          },
          toolTip: {
            shared: true
          },
          data: [{
            name: 'Buy Pressure',
            type: 'spline',
            yValueFormatString: "$####### M",
            showInLegend: true,
            color: "rgba(60,179,113, 1)",
            dataPoints: BuyPressure
          },
          {
            name: 'Sell Pressure',
            type: 'spline',
            yValueFormatString: "$####### M",
            showInLegend: true,
            color: "rgba(255,0,0, 1)",
            dataPoints: SellPressure
          }]
        })

        chart.render()
        var chart = new CanvasJS.Chart('BottomPlot', {
          animationEnabled: false,
          title: {
            text: 'Market Depth Ratio'
          },
          axisX: {
            valueFormatString: 'HH:mm'
          },
          axisY: {
            title: 'Percent',
            includeZero: true,
            suffix: ''
          },
          toolTip: {
            shared: true
          },
          data: [{
            name: 'MDR',
            type: 'spline',
            showInLegend: true,
            color: 'rgba(0,0,0, 1)',
            dataPoints: MDR
          }]
        })

        chart.render()
      }
    }
    )
}

function AutoUpdate () {
  PlotPressure(queryPlotPressure, 'LeftPlot')
  PlotMarketdepth(queryMarketDepth, 'RightPlot')
}

window.setInterval(function () {
  // Redraw the plots every 60 seconds
  if ($('#customSwitch1').is(':checked')) {
    AutoUpdate()
  }
}, 60000);


$('#plot').on('click', function () {
  // This function reads the text from forms and translates it to query
  var date
  queryPlotPressure = ''
  if (document.getElementById('coin').value !== '') queryPlotPressure += '&coin=' + document.getElementById('coin').value.toUpperCase()
  if (document.getElementById('exchange').value !== '') queryPlotPressure += '&exchange=' + document.getElementById('exchange').value
  if (document.getElementById('percentage').value !== '') queryPlotPressure += '&percent=' + document.getElementById('percentage').value
  queryMarketDepth = queryPlotPressure
  if (document.getElementById('datetimepicker_start').value !== '') {
    date = new Date(document.getElementById('datetimepicker_start').value.replace(' ', 'T'))
    queryPlotPressure += '&start_time=' + moment.utc(date).format('YYYY-MM-DD HH:mm')
  }
  if (document.getElementById('datetimepicker_end').value !== '') {
    date = new Date(document.getElementById('datetimepicker_end').value.replace(' ', 'T'))
    queryPlotPressure += '&end_time=' + moment.utc(date).format('YYYY-MM-DD HH:mm')
    queryPlotPressure += '&realtime=false'
    queryMarketDepth += '&start_time=' + moment.utc(date - 300000).format('YYYY-MM-DD HH:mm')
    queryMarketDepth += '&end_time=' + moment.utc(date).format('YYYY-MM-DD HH:mm')
    queryMarketDepth += '&realtime=false'
  }
  else {
    queryPlotPressure += '&realtime=true'
    queryMarketDepth += '&realtime=true'
  }
  AutoUpdate()
})
