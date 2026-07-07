document.getElementById('generator-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const apiBaseUrl = document.getElementById('apiBaseUrl').value.trim();
    const algorithm = document.getElementById('algorithm').value;
    const difficulty = document.getElementById('difficulty').value;
    const learningGoal = document.getElementById('learning_goal').value.trim();
    const userLevel = document.getElementById('user_level').value.trim();
    const minCases = parseInt(document.getElementById('min_cases').value) || 5;
    const allowedHintLevel = parseInt(document.getElementById('allowed_hint_level').value) || 3;
    const includeHints = document.getElementById('include_hints').checked;

    // Reset view states
    const resultPanel = document.getElementById('result-panel');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');

    resultPanel.classList.add('hidden');
    errorMessage.classList.add('hidden');
    loadingSpinner.classList.remove('hidden');

    const requestBody = {
        algorithm,
        difficulty,
        problem_style: "practical",
        language: "Python",
        learning_goal: learningGoal || null,
        user_level: userLevel || null,
        recent_weaknesses: [],
        min_cases: minCases,
        allowed_hint_level: allowedHintLevel,
        include_hints: includeHints
    };

    try {
        const response = await fetch(`${apiBaseUrl}/api/problems/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`HTTP 에러! 상태코드: ${response.status}`);
        }

        const data = await response.json();
        renderResponse(data);

        loadingSpinner.classList.add('hidden');
        resultPanel.classList.remove('hidden');
    } catch (err) {
        console.error(err);
        document.getElementById('error-text').innerText = `문제가 발생했습니다: ${err.message}`;
        loadingSpinner.classList.add('hidden');
        errorMessage.classList.remove('hidden');
    }
});

function renderResponse(data) {
    // Badges
    document.getElementById('badge-mode').innerText = `Gateway Mode: ${data.gateway_mode.toUpperCase()}`;
    const action = data.routing_decision?.action || 'unknown';
    document.getElementById('badge-action').innerText = `Action: ${action}`;

    // Problem details
    const problem = data.generated_problem || {};
    document.getElementById('prob-title').innerText = problem.title || '-';
    document.getElementById('prob-algo').innerText = (problem.algorithm || []).join(', ') || '-';
    document.getElementById('prob-diff').innerText = problem.difficulty || '-';
    document.getElementById('prob-goal').innerText = problem.learning_goal || '-';
    document.getElementById('prob-statement').innerText = problem.statement || '-';
    document.getElementById('prob-input-format').innerText = problem.input_format || '-';
    document.getElementById('prob-output-format').innerText = problem.output_format || '-';

    // Constraints
    const constraintsList = document.getElementById('prob-constraints');
    constraintsList.innerHTML = '';
    (problem.constraints || []).forEach(c => {
        const li = document.createElement('li');
        li.innerText = c;
        constraintsList.appendChild(li);
    });

    document.getElementById('prob-sample-input').innerText = problem.sample_input || '-';
    document.getElementById('prob-sample-output').innerText = problem.sample_output || '-';

    // Testcases
    const bundle = data.testcase_bundle || {};
    const testcases = bundle.testcases || [];
    document.getElementById('tc-count').innerText = testcases.length;

    const tcList = document.getElementById('tc-list');
    tcList.innerHTML = '';

    // Show first 3 testcases
    testcases.slice(0, 3).forEach((tc, idx) => {
        const tcCard = document.createElement('div');
        tcCard.className = 'tc-card';
        tcCard.innerHTML = `
            <div class="tc-header">
                <span class="tc-title">테스트케이스 #${idx + 1} (${tc.name})</span>
                <span class="badge">${tc.visibility}</span>
            </div>
            <div class="prob-section">
                <strong>설명/용도:</strong> ${tc.purpose || '-'}
            </div>
            <div class="form-row">
                <div>
                    <strong>입력:</strong>
                    <pre><code>${tc.input_data}</code></pre>
                </div>
                <div>
                    <strong>예상 출력:</strong>
                    <pre><code>${tc.expected_output}</code></pre>
                </div>
            </div>
        `;
        tcList.appendChild(tcCard);
    });

    if (testcases.length > 3) {
        const moreDiv = document.createElement('div');
        moreDiv.style.textAlign = 'center';
        moreDiv.style.color = 'var(--text-secondary)';
        moreDiv.style.fontSize = '0.9rem';
        moreDiv.innerText = `...외 ${testcases.length - 3}개의 테스트케이스가 더 있습니다.`;
        tcList.appendChild(moreDiv);
    }

    // Validation & Routing
    const validation = data.validation_report || {};
    const decision = data.routing_decision || {};

    document.getElementById('val-passed').innerText = validation.passed !== undefined ? validation.passed : '-';
    document.getElementById('val-action').innerText = decision.action || '-';
    document.getElementById('val-reason').innerText = decision.reason || '-';

    // Raw JSON
    document.getElementById('json-raw').innerText = JSON.stringify(data, null, 2);
}
