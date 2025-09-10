let lstmChartInstance; // Chart.js instance for LSTM
let sentimentChartInstance; // Chart.js instance for Sentiment

/**
 * Updates the current time displayed in the header.
 */
function updateTime() {
    document.getElementById('currentTime').textContent = new Date().toLocaleString();
}
// Update time every second
setInterval(updateTime, 1000);
// Initial call to display time immediately
updateTime();

/**
 * Helper function to get decision icon SVG based on decision.
 * @param {string} decision - The investment decision (BUY, SELL, HOLD).
 * @returns {string} SVG string for the icon.
 */
function getDecisionIcon(decision) {
    switch (decision.toUpperCase()) {
        case 'BUY':
            return `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2">
                                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                                <polyline points="17 6 23 6 23 12"></polyline>
                            </svg>`;
        case 'SELL':
            return `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2">
                                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
                                <polyline points="17 18 23 18 23 12"></polyline>
                            </svg>`;
        case 'HOLD':
            return `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="16" x2="12" y2="8"></line>
                                <line x1="8" y1="12" x2="16" y2="12"></line>
                            </svg>`;
        default:
            return `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>`;
    }
}

/**
 * Renders or updates a Chart.js line chart.
 * @param {string} canvasId - The ID of the canvas element.
 * @param {Array<number>} data - The data points for the chart.
 * @param {Array<string>} labels - The labels for the x-axis.
 * @param {string} borderColor - The color of the line.
 * @param {string} chartTitle - The title of the chart.
 * @returns {Chart} The Chart.js instance.
 */
function renderLineChart(canvasId, data, labels, borderColor, chartTitle) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    let chartInstance;

    // Destroy existing chart instance if it exists
    if (canvasId === 'lstmChart' && lstmChartInstance) {
        lstmChartInstance.destroy();
    } else if (canvasId === 'sentimentChart' && sentimentChartInstance) {
        sentimentChartInstance.destroy();
    }

    const newChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: chartTitle,
                data: data,
                borderColor: borderColor,
                borderWidth: 2,
                fill: false,
                tension: 0.3,
                pointBackgroundColor: borderColor,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: borderColor,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: '#cbd5e1'
                    },
                    ticks: {
                        color: '#484848'
                    }
                },
                y: {
                    grid: {
                        color: '#cbd5e1'
                    },
                    ticks: {
                        color: '#484848'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#e2e8f0',
                    bodyColor: '#e2e8f0',
                    borderColor: '#4f46e5',
                    borderWidth: 1
                }
            }
        }
    });

    if (canvasId === 'lstmChart') {
        lstmChartInstance = newChart;
    } else if (canvasId === 'sentimentChart') {
        sentimentChartInstance = newChart;
    }
    return newChart;
}

/**
 * Populates the event list dynamically.
 * @param {Array<Object>} events - An array of event objects.
 */
function populateEventList(events) {
    const eventListContainer = document.getElementById('eventList');
    eventListContainer.innerHTML = ''; // Clear existing events

    events.forEach(event => {
        const eventItem = `
                    <div class="event-item">
                        <div class="event-indicator" style="background: #ffcc15;"></div>
                        <div style="font-size: 0.95rem; font-weight: 500; color: #7c8b9e;">${event}</div>
                    </div>
                `;
        eventListContainer.insertAdjacentHTML('beforeend', eventItem);
    });
}

/**
 * Populates the key decision factors dynamically.
 * @param {Array<string>} factors - An array of factor strings.
 */
function populateKeyFactors(factors) {
    const keyFactorsGrid = document.getElementById('keyFactorsGrid');
    keyFactorsGrid.innerHTML = ''; // Clear existing factors

    factors.forEach((factor, index) => {
        const factorCard = `
                    <div class="factor-card">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <div class="factor-number">${index + 1}</div>
                            <span style="font-size: 0.85rem; font-weight:bold; color: #484848;">Factor ${index + 1}</span>
                        </div>
                        <p style="font-size: 0.95rem; color: #7c8b9e;">${factor}</p>
                    </div>
                `;
        keyFactorsGrid.insertAdjacentHTML('beforeend', factorCard);
    });
}

/**
 * Fetches and updates all dashboard data from the backend.
 */
async function refreshAnalysis() {
    console.log('Fetching dashboard data...');
    const refreshButton = document.getElementById('refreshBtn');
    // Store original button text and disable it during fetch
    const originalButtonText = refreshButton.textContent;
    refreshButton.textContent = 'Refreshing...';
    refreshButton.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:8000/dashboard_data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Data fetched successfully:', data);

        // --- Update Main Info ---
        document.getElementById('date').textContent = data.main_info.date;
        document.getElementById('date').style.fontWeight = '700'; // Keep font weight

        document.getElementById('lastPrice').textContent = data.main_info.last_price;
        document.getElementById('lastPrice').style.fontWeight = '700'; // Keep font weight

        // --- Update Main Decision Section ---
        document.getElementById('investmentDecision').textContent = data.main_decision.decision;
        const decisionIconContainer = document.getElementById('decisionIcon');
        decisionIconContainer.innerHTML = getDecisionIcon(data.main_decision.decision);
        decisionIconContainer.querySelector('svg').style.stroke = data.main_decision.decision_color;
        document.getElementById('investmentDecision').style.color = data.main_decision.decision_color;
        document.getElementById('investmentDecision').style.textShadow = `0 0 25px ${data.main_decision.decision_color}66`; // Add glow effect
        decisionIconContainer.style.boxShadow = `0 0 40px ${data.main_decision.decision_color}66`;


        const confidence = data.main_decision.confidence;
        document.getElementById('confidenceText').textContent = `${confidence}%`;
        const circumference = 2 * Math.PI * 56; // 56 is the radius
        const offset = circumference - (confidence / 100) * circumference;
        const confidenceProgress = document.getElementById('confidenceProgress');
        confidenceProgress.style.strokeDashoffset = offset;
        confidenceProgress.style.stroke = data.main_decision.confidence_color;
        confidenceProgress.style.filter = `drop-shadow(0 0 15px ${data.main_decision.confidence_color}99)`;


        document.getElementById('aiReasoning').textContent = data.main_decision.ai_reasoning;

        populateKeyFactors(data.main_decision.key_factors);

        // --- Update LSTM Prediction ---
        document.getElementById('lstmPredictionScore').textContent = data.lstm_prediction.prediction_score.toFixed(2);
        document.getElementById('lstmPredictionInterval').textContent = data.lstm_prediction.prediction_interval;
        renderLineChart('lstmChart', data.lstm_prediction.chart_data, data.lstm_prediction.chart_labels, '#22c55e', 'LSTM Prediction');

        // --- Update Social Sentiment ---
        document.getElementById('sentimentScore').textContent = data.social_sentiment.sentiment_score.toFixed(3);
        renderLineChart('sentimentChart', data.social_sentiment.chart_data, data.social_sentiment.chart_labels, '#4f46e5', 'Sentiment Trend');
        document.getElementById('sentimentSummary').textContent = data.social_sentiment.summary;

        // --- Update Event Impact ---
        populateEventList(data.event_impact.events);

        // --- Update Memory Bank Insights ---
        document.getElementById('scenariosFound').textContent = data.memory_bank.scenarios_found;
        document.getElementById('successRate').textContent = `${data.memory_bank.success_rate}%`;
        document.getElementById('memoryInsight').textContent = data.memory_bank.insight;

    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Instead of an alert, update a visible status message
        // You might want a dedicated area for messages, e.g., <div id="statusMessage"></div>
        // document.getElementById('statusMessage').textContent = 'Failed to load dashboard data. Please check the backend server.';
        alert('Failed to load dashboard data. Please check the backend server.');
    } finally {
        refreshButton.textContent = originalButtonText; // Restore original text
        refreshButton.disabled = false;
    }
}

// Function to handle report download 
async function downloadReport() {
    // Check current date first
    date = document.getElementById('date').textContent;

    //call backemd function to fetch the report
    console.log('Retrieving Full Investment Report...');
    const downloadButton = document.getElementById('downloadBtn');
    // Store original button text and disable it during fetch
    const originalButtonText = downloadButton.textContent;
    downloadButton.textContent = 'Refreshing...';
    downloadButton.disabled = true;

    try {
        const response = await fetch(`http://127.0.0.1:8000/download_report?end_date=${date}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.text();
        console.log('Report downloaded successfully:', data);

        // Create a blob and trigger download
        const blob = new Blob([data], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "investment_report_" + date + ".txt";  // filename
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Error downloading investment report:', error);
        alert('Failed to load investment report. Please check the backend server.');

    } finally {
        downloadButton.textContent = originalButtonText; // Restore original text
        downloadButton.disabled = false;
    }
}

// Initial data load when the page loads
document.addEventListener('DOMContentLoaded', () => {
    refreshAnalysis(); // Call once immediately when the page loads

    // Set up interval to call refreshAnalysis every 10 seconds (10000 milliseconds)
    setInterval(refreshAnalysis, 10000000000);
});