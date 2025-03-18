const customDarkTheme = {
  backgroundColor: '#1a1e26',
  textStyle: {
    color: '#fff'
  },
  title: {
    textStyle: {
      color: '#000000'
    }
  },
};

const chartDom = document.getElementById('accumulationCurveChart');
const myChart = echarts.init(chartDom, customDarkTheme);
const option = {
  title: {
    text: 'Species Accumulation Curve',
    left: 'center',
    textStyle: {
      color: '#fff',
    },
    top: '15px',
  },
  grid: {
    left: '10%',
    right: '5%',
  },
  xAxis: {
    type: 'category',
    name: 'Hours',
    nameLocation: 'middle',
    nameGap: '40',
    data: Array.from({ length: tofa.deployment_time }, (_, i) => i + 1),
  },
  yAxis: {
    type: 'value',
    name: 'Unique Taxa',
    nameLocation: 'middle',
    nameGap: '30',
    splitLine: {
      lineStyle: {
        color: 'rgba(255,255,255,0.50)',
      },
    },
  },
  series: [
    {
      data: tofa.accumulation_data,
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#00adb5',
      },
      itemStyle: {
        color: '#00adb5',
      }
    },
  ],
};

option && myChart.setOption(option);
