

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


document.getElementById('recalculate').addEventListener('click', function() {
    fetch('/recalculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'start_date': document.getElementById('start_date').value,
            'end_date': document.getElementById('end_date').value
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Update your chart data here

        myChart.data.labels = data.labels;
        myChart.data.datasets[0].data = data.data;
        myChart.update();
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});