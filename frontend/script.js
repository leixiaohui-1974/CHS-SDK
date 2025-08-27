// script.js - 通用算法测试界面的交互逻辑

// --- Data Definitions ---
const ALGORITHM_PARAMS = {
    pid_controller: {
        name: 'PID 控制算法',
        params: [
            { id: 'kp', label: 'Kp (比例)', type: 'number', value: 1.0, step: 0.1 },
            { id: 'ki', label: 'Ki (积分)', type: 'number', value: 0.5, step: 0.1 },
            { id: 'kd', label: 'Kd (微分)', type: 'number', value: 0.1, step: 0.05 },
        ]
    },
    dmpc_controller: {
        name: 'DMPC 控制算法',
        params: [
            { id: 'prediction_horizon', label: '预测时域 (步)', type: 'number', value: 10, step: 1 },
            { id: 'control_horizon', label: '控制时域 (步)', type: 'number', value: 3, step: 1 },
            { id: 'q_weight', label: 'Q (状态权重)', type: 'number', value: 1, step: 0.5 },
            { id: 'r_weight', label: 'R (控制权重)', type: 'number', value: 0.1, step: 0.1 },
        ]
    },
    data_cleaning_algorithm: {
        name: '数据清洗算法',
        params: [
            { id: 'window_size', label: '滑动窗口大小', type: 'number', value: 5, step: 1 },
            { id: 'std_dev_threshold', label: '标准差阈值', type: 'number', value: 3, step: 0.5 },
        ]
    }
};

// --- Global State ---
let simulationChart;
let simulationInterval;
let currentTime = 0;

// --- DOM Ready ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded. Initializing components.");
    // Initialize UI components
    initializeChart();
    initializeEventListeners();
    // Set default state
    updateAlgorithmParams();
});

// --- Initializers ---
function initializeEventListeners() {
    document.getElementById('algorithm-selector').addEventListener('change', updateAlgorithmParams);
    document.getElementById('run-test-btn').addEventListener('click', runTest);
    document.getElementById('generate-disturbance-btn').addEventListener('click', generateDisturbance);
    document.getElementById('generate-report-btn').addEventListener('click', generateDiagnosisReport);
}

function initializeChart() {
    const ctx = document.getElementById('simulation-chart').getContext('2d');
    if (!ctx) {
        console.error("Chart context not found.");
        return;
    }
    simulationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: '上游水位 (m)', data: [], borderColor: 'rgb(54, 162, 235)', yAxisID: 'y', tension: 0.1 },
                { label: '下游水位 (m)', data: [], borderColor: 'rgb(255, 206, 86)', yAxisID: 'y', tension: 0.1 },
                { label: '闸门开度 (%)', data: [], borderColor: 'rgb(75, 192, 192)', yAxisID: 'y1', tension: 0.1 },
                { label: '入流流量 (m³/s)', data: [], borderColor: 'rgb(255, 99, 132)', yAxisID: 'y2', borderDash: [5, 5], tension: 0.1 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
            scales: {
                x: { display: true, title: { display: true, text: '时间 (s)' } },
                y: { type: 'linear', display: true, position: 'left', title: { display: true, text: '水位 (m)' } },
                y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: '开度 (%)' }, grid: { drawOnChartArea: false }, min: 0, max: 100 },
                y2: { type: 'linear', display: false, position: 'right', title: { display: true, text: '流量 (m³/s)' } }
            },
            plugins: { legend: { position: 'top' }, title: { display: true, text: '系统状态动态曲线' } }
        }
    });
}

// --- UI Update Functions ---
function updateAlgorithmParams() {
    const selector = document.getElementById('algorithm-selector');
    const selectedAlgorithm = selector.value;
    const paramsContainer = document.getElementById('algorithm-params');
    paramsContainer.innerHTML = ''; // Clear previous params

    const algorithm = ALGORITHM_PARAMS[selectedAlgorithm];
    if (!algorithm) return;

    algorithm.params.forEach(param => {
        const paramGroup = document.createElement('div');
        paramGroup.classList.add('param-group');
        const label = document.createElement('label');
        label.htmlFor = param.id;
        label.textContent = param.label;
        const input = document.createElement('input');
        input.type = param.type;
        input.id = param.id;
        input.name = param.id;
        input.value = param.value;
        if (param.step) input.step = param.step;

        paramGroup.appendChild(label);
        paramGroup.appendChild(input);
        paramsContainer.appendChild(paramGroup);
    });
}

// --- Simulation Logic ---
function runTest() {
    if (simulationInterval) {
        clearInterval(simulationInterval);
    }
    resetSimulation();

    const runBtn = document.getElementById('run-test-btn');
    runBtn.textContent = '测试中...';
    runBtn.disabled = true;

    simulationInterval = setInterval(simulationStep, 500);

    // Stop simulation after 20 steps (10 seconds)
    setTimeout(() => {
        clearInterval(simulationInterval);
        simulationInterval = null;
        runBtn.textContent = '运行测试';
        runBtn.disabled = false;
        updateKpiTable();
        console.log("Simulation finished.");
    }, 10000);
}

function resetSimulation() {
    currentTime = 0;
    simulationChart.data.labels = [];
    simulationChart.data.datasets.forEach(dataset => {
        dataset.data = [];
    });
    simulationChart.update();
    // Reset animation
    document.querySelector('#upstream-pool .water-level').style.height = `60%`;
    document.querySelector('#downstream-pool .water-level').style.height = `50%`;
    document.querySelector('#gate').style.height = `80%`;
    // Reset KPIs
    document.querySelector('[data-kpi="overshoot"]').textContent = '-';
    document.querySelector('[data-kpi="recovery_time"]').textContent = '-';
    document.querySelector('[data-kpi="steady_error"]').textContent = '-';
}

function simulationStep() {
    currentTime++;
    const timeLabel = `${currentTime * 0.5}s`;

    // Mock data generation
    const upstreamLevel = 3.0 + Math.sin(currentTime / 5) * 0.2 + (Math.random() - 0.5) * 0.1;
    const downstreamLevel = 3.5 - Math.sin(currentTime / 8) * 0.15 + (Math.random() - 0.5) * 0.1;
    const gateOpening = 50 + Math.cos(currentTime / 6) * 20 + (Math.random() - 0.5) * 5;
    const inflow = 5.0 + (currentTime > 5 && currentTime < 15 ? 5.0 : 0.0); // Step disturbance

    // Update Chart
    simulationChart.data.labels.push(timeLabel);
    simulationChart.data.datasets[0].data.push(upstreamLevel.toFixed(2));
    simulationChart.data.datasets[1].data.push(downstreamLevel.toFixed(2));
    simulationChart.data.datasets[2].data.push(gateOpening.toFixed(2));
    simulationChart.data.datasets[3].data.push(inflow.toFixed(2));
    simulationChart.update();

    // Update Animation
    document.querySelector('#upstream-pool .water-level').style.height = `${(upstreamLevel / 5) * 100}%`;
    document.querySelector('#downstream-pool .water-level').style.height = `${(downstreamLevel / 5) * 100}%`;
    document.querySelector('#gate').style.height = `${100 - gateOpening}%`;
}

function updateKpiTable() {
    document.querySelector('[data-kpi="overshoot"]').textContent = '0.25m';
    document.querySelector('[data-kpi="recovery_time"]').textContent = '8.5s';
    document.querySelector('[data-kpi="steady_error"]').textContent = '0.05m';

    document.querySelector('[data-kpi-status="overshoot"]').textContent = '否';
    document.querySelector('[data-kpi-status="recovery_time"]').textContent = '是';
    document.querySelector('[data-kpi-status="steady_error"]').textContent = '是';
}

// --- LLM Simulation Functions ---
function generateDisturbance() {
    const timeline = document.getElementById('disturbance-timeline');
    timeline.innerHTML = `<pre>${JSON.stringify(
    [{
        "start_time": 5,
        "disturbance_type": "inflow_change",
        "parameters": { "target_inflow": 10, "duration": 10 }
    }], null, 2)}</pre>`;
}

function generateDiagnosisReport() {
    const reportContainer = document.getElementById('diagnosis-report');
    const prompt = document.getElementById('diagnosis-prompt').value;
    if (prompt.includes("PID")) {
        reportContainer.innerHTML = `
            <h4>诊断报告</h4>
            <p><strong>诊断结果:</strong> 控制器性能不佳，出现持续振荡。</p>
            <p><strong>根源分析:</strong> 在系统受到阶跃扰动后，PID参数中的积分项(Ki)设置过高，导致系统响应过快产生超调，而微分项(Kd)不足以抑制振荡，最终形成持续等幅振荡。</p>
            <p><strong>改进建议:</strong>
                <ul>
                    <li>适当减小积分增益 (Ki) 以降低超调。</li>
                    <li>增大微分增益 (Kd) 以增强系统阻尼，加快振荡衰减。</li>
                    <li>建议Ki从0.5调整至0.2，Kd从0.1调整至0.3后再次测试。</li>
                </ul>
            </p>`;
    } else {
        reportContainer.textContent = "分析完成：未检测到明显问题或无法根据输入生成报告。";
    }
}
