function plot_marketdepth (query, CanvasName) {
  fetch('https://cors-anywhere.herokuapp.com/https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1?output=marketdepth' + query, {
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
        for (var i = 0.0; i < 20.0; i += 0.2) {
          if (i.toFixed(2) in data.orders) {
            AsksTotal += parseFloat(data.orders[i.toFixed(2)])
          }
          if ((-i).toFixed(2) in data.orders) {
            BidsTotal += parseFloat(data.orders[(-i).toFixed(2)])
          }
          if (i === 0.0) { i = 0.001 }
          AsksDataPoints.push({ x: i, y: AsksTotal })
          BidsDataPoints.push({ x: -i, y: BidsTotal })
        }
        var chart = new CanvasJS.Chart(CanvasName, {
          animationEnabled: true,
          title: {
            text: 'Crypto Market Depth'
          },
          axisY: {
            title: 'US Dollar',
            valueFormatString: '#0,.',
            suffix: 'k'
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
            toolTipContent: '<span style="color:#3CB371"><strong>{name}: </strong></span> {y}',
            name: 'Asks',
            dataPoints: AsksDataPoints
          },
          {
            type: 'stackedArea',
            name: 'Bids',
            toolTipContent: '<span style="color:#4F81BC"><strong>{name}: </strong></span> {y}<br><b>Total:<b> #total',
            showInLegend: true,
            dataPoints: BidsDataPoints
          }]
        })
        chart.render()
      }
    }
    )
}

function plot_pressure (query, CanvasName) {
  fetch('https://cors-anywhere.herokuapp.com/https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1?output=mdr' + query, {
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
        for (var key in data) {
          var date = key.split(' ')
          BuyPressure.push({ x: new Date(date[0] + 'T' + date[1] + ':00Z'), y: parseFloat(data[key]['Buy Pressure']) })
          SellPressure.push({ x: new Date(date[0] + 'T' + date[1] + ':00Z'), y: parseFloat(data[key]['Sell Pressure']) })
        }
        var chart = new CanvasJS.Chart(CanvasName, {
          animationEnabled: true,
          title: {
            text: 'Buy/Sell Pressure'
          },
          axisX: {
            valueFormatString: 'HH:mm'
          },
          axisY: {
            title: 'USD',
            includeZero: true,
            suffix: ' USD'
          },
          toolTip: {
            shared: true
          },
          data: [{
            name: 'Buy Pressure',
            type: 'spline',
            yValueFormatString: "$#######.00",
            showInLegend: true,
            dataPoints: BuyPressure
          },
          {
            name: 'Sell Pressure',
            type: 'spline',
            yValueFormatString: "$#######.00",
            showInLegend: true,
            dataPoints: SellPressure
          }]
        })

        chart.render()
      }
    }
    )
}

function historical () {
  plot_marketdepth('&coin=BTC&exchange=bitfinex&start_time=2019-02-06%2004:58&end_time=2019-02-06%2004:58', 'RightPlot')
}

function RealTime () {
  plot_pressure('&realtime=true', 'LeftPlot')
  plot_marketdepth('&realtime=true', 'RightPlot')
}

$('#historical').change(function () {
  if ($('#historical').is(':checked')) { historical() }
  else { RealTime() }
}
)

$('#plot').on('click', function () {
  var query = '&realtime=false'
  if (document.getElementById('market').value !== '') query += '&market=' + document.getElementById('market').value
  if (document.getElementById('exchange').value !== '') query += '&exchange=' + document.getElementById('exchange').value
  if (document.getElementById('datetimepicker_start').value !== '') query += '&start_time=' + document.getElementById('datetimepicker_start').value
  if (document.getElementById('datetimepicker_end').value !== '') query += '&end_time=' + document.getElementById('datetimepicker_end').value
  if (document.getElementById('percentage').value !== '') query += '&percent=' + document.getElementById('percentage').value
  plot_pressure(query, 'LeftPlot')
})
