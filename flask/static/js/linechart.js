

const chartData = {
    labels: labels,
    datasets: [{
        label: chartLabel,
        backgroundColor: 'rgb(255, 99, 132)',
        borderColor: 'rgb(255, 99, 132)',
        data: data,
    }]
};

const config = {
    type: 'line',
    data: chartData,
    options: { maintainAspectRatio: false }
};

const myChart = new Chart(
    document.getElementById('myChart'),
    config
);