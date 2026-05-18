const state = {
    metrics: {
        queued: 0,
        running: 0,
        completed: 0,
        failed: 0,
        recovered: 0,
        cancelled: 0,
        total: 0,
        backlog: 0
    },
    service: {
        live: "checking",
        ready: "checking"
    },
    orders: [],
    selectedOrderId: null,
    activity: [],
    burstInFlight: false,
    retryInFlight: false
};

const templates = {
    campus: {
        customerName: "Ayush",
        restaurantName: "Campus Canteen",
        pickupAddress: "Block A",
        deliveryAddress: "Hostel Gate",
        items: ["Paneer Roll", "Cold Coffee"],
        priority: 5,
        estimatedDistanceKm: 2.5,
        simulateSeconds: 2,
        forceFail: false
    },
    express: {
        customerName: "Nisha",
        restaurantName: "Express Bites",
        pickupAddress: "Library Lane",
        deliveryAddress: "Innovation Hostel",
        items: ["Wrap", "Fresh Juice"],
        priority: 8,
        estimatedDistanceKm: 1.4,
        simulateSeconds: 1,
        forceFail: false
    },
    chaos: {
        customerName: "Recovery Demo",
        restaurantName: "Metro Biryani",
        pickupAddress: "North Gate",
        deliveryAddress: "Systems Lab",
        items: ["Veg Biryani", "Raita"],
        priority: 9,
        estimatedDistanceKm: 4.7,
        simulateSeconds: 3,
        forceFail: true
    }
};

const burstRestaurants = [
    ["Campus Canteen", "Campus Pickup", ["Paneer Roll", "Cold Coffee"]],
    ["Metro Biryani", "North Gate", ["Veg Biryani", "Raita"]],
    ["Green Bowl", "Fitness Block", ["Rice Bowl", "Lassi"]],
    ["Pizza Corner", "Food Court", ["Margherita Pizza", "Iced Tea"]]
];

const $ = (id) => document.getElementById(id);

function nowStamp() {
    return new Date().toLocaleTimeString([], { hour12: false });
}

function pushActivity(title, message) {
    state.activity.unshift({
        time: nowStamp(),
        title,
        message
    });
    state.activity = state.activity.slice(0, 10);
    renderActivity();
}

function setTemplate(name) {
    const template = templates[name];
    if (!template) {
        return;
    }

    $("customerName").value = template.customerName;
    $("restaurantName").value = template.restaurantName;
    $("pickupAddress").value = template.pickupAddress;
    $("deliveryAddress").value = template.deliveryAddress;
    $("items").value = template.items.join(", ");
    $("priority").value = String(template.priority);
    $("priorityDisplay").textContent = `${template.priority} / 10`;
    $("estimatedDistanceKm").value = String(template.estimatedDistanceKm);
    $("simulateSeconds").value = String(template.simulateSeconds);
    $("forceFail").checked = template.forceFail;

    pushActivity("Template loaded", `${name} preset copied into the order form.`);
}

function readFormPayload() {
    return {
        customerName: $("customerName").value.trim(),
        restaurantName: $("restaurantName").value.trim(),
        pickupAddress: $("pickupAddress").value.trim(),
        deliveryAddress: $("deliveryAddress").value.trim(),
        items: $("items").value
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        priority: Number($("priority").value),
        estimatedDistanceKm: Number($("estimatedDistanceKm").value),
        simulateSeconds: Number($("simulateSeconds").value),
        forceFail: $("forceFail").checked
    };
}

function randomPayload(index) {
    const base = readFormPayload();
    const variant = burstRestaurants[index % burstRestaurants.length];
    return {
        ...base,
        customerName: `${base.customerName || "Customer"} ${index + 1}`,
        restaurantName: variant[0],
        pickupAddress: variant[1],
        deliveryAddress: `${base.deliveryAddress || "Hostel Gate"} ${1 + (index % 4)}`,
        items: variant[2],
        priority: Math.max(1, Math.min(10, base.priority + (index % 3) - 1)),
        estimatedDistanceKm: Number((base.estimatedDistanceKm + (index % 5) * 0.4).toFixed(1)),
        simulateSeconds: Math.max(1, Math.min(30, base.simulateSeconds + (index % 4)))
    };
}

async function requestJson(url, options) {
    const response = await fetch(url, options);
    const payload = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) {
        const message = payload && payload.detail ? payload.detail : `Request failed with ${response.status}`;
        throw new Error(message);
    }
    return payload;
}

async function pollPlatform() {
    try {
        const [health, ready, metrics, orders] = await Promise.all([
            requestJson("/healthz"),
            fetch("/readyz").then(async (response) => ({
                ok: response.ok,
                payload: await response.json().catch(() => ({ status: "unknown" }))
            })),
            requestJson("/metrics"),
            requestJson("/orders?limit=14")
        ]);

        state.service.live = health.status || "unknown";
        state.service.ready = ready.ok ? ready.payload.status : "not-ready";
        state.metrics = metrics || state.metrics;
        state.orders = Array.isArray(orders) ? orders : [];

        if (!state.selectedOrderId && state.orders.length > 0) {
            state.selectedOrderId = state.orders[0].job_id;
        }

        render();
    } catch (error) {
        state.service.live = "down";
        state.service.ready = "not-ready";
        $("liveNote").textContent = error.message;
        $("readyNote").textContent = "Backend polling failed";
        renderStatus();
    }
}

function renderStatus() {
    const liveStatus = $("liveStatus");
    const readyStatus = $("readyStatus");
    const metrics = state.metrics;

    liveStatus.textContent = state.service.live;
    liveStatus.className = "status-value";
    if (state.service.live === "ok") {
        liveStatus.classList.add("status-ok");
        $("liveNote").textContent = "Order API responding";
    } else {
        liveStatus.classList.add("status-down");
        $("liveNote").textContent = $("liveNote").textContent || "Order API unavailable";
    }

    readyStatus.textContent = state.service.ready;
    readyStatus.className = "status-value";
    if (state.service.ready === "ready") {
        readyStatus.classList.add("status-ok");
        $("readyNote").textContent = "Redis dependency reachable";
    } else {
        readyStatus.classList.add("status-warn");
        $("readyNote").textContent = "Dependency or startup issue";
    }

    $("totalOrders").textContent = String(metrics.total ?? 0);
    $("backlogValue").textContent = String(metrics.backlog ?? 0);
    $("refreshTime").textContent = nowStamp();

    $("metricQueued").textContent = String(metrics.queued ?? 0);
    $("metricRunning").textContent = String(metrics.running ?? 0);
    $("metricCompleted").textContent = String(metrics.completed ?? 0);
    $("metricFailed").textContent = String(metrics.failed ?? 0);
    $("metricRecovered").textContent = String(metrics.recovered ?? 0);
    $("metricCancelled").textContent = String(metrics.cancelled ?? 0);

    const total = Math.max(metrics.total || 0, 1);
    const segments = {
        queued: ((metrics.queued || 0) / total) * 100,
        running: ((metrics.running || 0) / total) * 100,
        completed: ((metrics.completed || 0) / total) * 100,
        failed: ((metrics.failed || 0) / total) * 100,
        recovered: ((metrics.recovered || 0) / total) * 100
    };

    $("barQueued").style.width = `${segments.queued}%`;
    $("barRunning").style.width = `${segments.running}%`;
    $("barCompleted").style.width = `${segments.completed}%`;
    $("barFailed").style.width = `${segments.failed}%`;
    $("barRecovered").style.width = `${segments.recovered}%`;
    $("barSummary").textContent = `${metrics.total || 0} tracked jobs`;
}

function statusClass(status) {
    return {
        queued: "status-queued",
        running: "status-running",
        completed: "status-completed",
        failed: "status-failed",
        recovered: "status-recovered",
        cancelled: "status-cancelled"
    }[status] || "status-queued";
}

function formatTime(value) {
    if (!value) {
        return "--";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

function renderOrders() {
    const body = $("ordersTableBody");
    if (state.orders.length === 0) {
        body.innerHTML = '<tr><td colspan="6" class="empty-state">No orders yet. Submit one from the form above.</td></tr>';
        renderDetail(null);
        return;
    }

    body.innerHTML = state.orders.map((order) => {
        const payload = order.payload || {};
        const selectedClass = order.job_id === state.selectedOrderId ? "active" : "";
        return `
            <tr class="${selectedClass}" data-order-id="${order.job_id}">
                <td><strong>${order.job_id.slice(0, 8)}</strong><br><small>${order.trace_id ? order.trace_id.slice(0, 8) : "--"}</small></td>
                <td>${payload.customer_name || "--"}</td>
                <td>${payload.restaurant_name || "--"}</td>
                <td><span class="status-badge ${statusClass(order.status)}">${order.status}</span></td>
                <td>${order.attempts ?? 0}</td>
                <td>${formatTime(order.updated_at)}</td>
            </tr>
        `;
    }).join("");

    body.querySelectorAll("tr[data-order-id]").forEach((row) => {
        row.addEventListener("click", () => {
            state.selectedOrderId = row.dataset.orderId;
            renderOrders();
        });
    });

    const selected = state.orders.find((order) => order.job_id === state.selectedOrderId) || state.orders[0];
    if (selected) {
        state.selectedOrderId = selected.job_id;
    }
    renderDetail(selected);
}

function renderDetail(order) {
    if (!order) {
        $("detailOrderId").textContent = "--";
        $("detailTraceId").textContent = "--";
        $("detailUpdated").textContent = "--";
        $("detailStatus").textContent = "No selection";
        $("detailStatus").className = "detail-pill";
        $("detailHint").textContent = "Select a failed order to resubmit it with failure injection disabled.";
        $("retryOrderButton").disabled = true;
        $("retryOrderButton").textContent = "Retry Failed Order";
        $("detailPayload").textContent = "Select an order to inspect payload.";
        $("detailResult").textContent = "Select an order to inspect result.";
        return;
    }

    $("detailOrderId").textContent = order.job_id || "--";
    $("detailTraceId").textContent = order.trace_id || "--";
    $("detailUpdated").textContent = formatTime(order.updated_at);
    $("detailStatus").textContent = order.status || "unknown";
    $("detailStatus").className = `detail-pill ${statusClass(order.status)}`;
    const canRetry = order.status === "failed" && !state.retryInFlight;
    $("retryOrderButton").disabled = !canRetry;
    $("retryOrderButton").textContent = order.status === "failed" ? "Retry Failed Order" : "Retry Unavailable";
    if (order.status === "failed") {
        if (order.recovery_job_id) {
            $("detailHint").textContent = `Recovery job ${order.recovery_job_id} was already submitted for this failure.`;
        } else {
            $("detailHint").textContent = "This will submit a fresh retry order with force-fail turned off.";
        }
    } else {
        $("detailHint").textContent = "Only failed orders can be retried.";
    }
    $("detailPayload").textContent = JSON.stringify(order.payload || {}, null, 2);
    $("detailResult").textContent = JSON.stringify({
        result: order.result,
        error: order.error,
        recovery_job_id: order.recovery_job_id || null,
        recovery_status: order.recovery_status || null,
        retry_of: order.retry_of || null
    }, null, 2);
}

function renderActivity() {
    const feed = $("activityFeed");
    feed.innerHTML = state.activity.map((entry) => `
        <article class="activity-item">
            <span class="activity-time">${entry.time}</span>
            <div>
                <strong>${entry.title}</strong>
                <p>${entry.message}</p>
            </div>
        </article>
    `).join("");
}

function render() {
    renderStatus();
    renderOrders();
}

async function submitOrder(event) {
    event.preventDefault();
    const button = $("submitOrderButton");
    const payload = readFormPayload();
    button.disabled = true;
    button.textContent = "Submitting...";

    try {
        const response = await requestJson("/orders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        state.selectedOrderId = response.order_id;
        pushActivity(
            payload.forceFail ? "Failure order queued" : "Order queued",
            `Order ${response.order_id} accepted with trace ${response.trace_id}.`
        );
        await pollPlatform();
    } catch (error) {
        pushActivity("Order submission failed", error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Submit Order";
    }
}

async function runBurst() {
    if (state.burstInFlight) {
        return;
    }

    const count = Math.max(1, Number($("burstCount").value) || 1);
    const concurrency = Math.max(1, Number($("burstConcurrency").value) || 1);
    const button = $("burstButton");
    state.burstInFlight = true;
    button.disabled = true;
    button.textContent = "Running...";

    let submitted = 0;
    let failed = 0;
    const jobs = Array.from({ length: count }, (_, index) => index);

    async function workerLoop() {
        while (jobs.length > 0) {
            const index = jobs.shift();
            const payload = randomPayload(index);
            try {
                await requestJson("/orders", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                submitted += 1;
            } catch (error) {
                failed += 1;
            }
        }
    }

    try {
        await Promise.all(Array.from({ length: Math.min(concurrency, count) }, workerLoop));
        pushActivity(
            "Burst completed",
            `${submitted} orders submitted with concurrency ${concurrency}${failed ? `, ${failed} failed` : ""}.`
        );
        await pollPlatform();
    } catch (error) {
        pushActivity("Burst failed", error.message);
    } finally {
        state.burstInFlight = false;
        button.disabled = false;
        button.textContent = "Run Burst";
    }
}

async function retrySelectedOrder() {
    const order = state.orders.find((entry) => entry.job_id === state.selectedOrderId);
    if (!order || order.status !== "failed" || state.retryInFlight) {
        return;
    }

    const button = $("retryOrderButton");
    state.retryInFlight = true;
    button.disabled = true;
    button.textContent = "Retrying...";

    try {
        const response = await requestJson(`/orders/${order.job_id}/retry`, {
            method: "POST"
        });
        state.selectedOrderId = response.order_id;
        pushActivity(
            "Recovery job queued",
            `Retry order ${response.order_id} created from failed order ${response.retried_from}.`
        );
        await pollPlatform();
    } catch (error) {
        pushActivity("Retry failed", error.message);
    } finally {
        state.retryInFlight = false;
        renderDetail(state.orders.find((entry) => entry.job_id === state.selectedOrderId) || order);
    }
}

async function copyPlaybookCommand(button) {
    const command = button.dataset.copy;
    if (!command) {
        return;
    }

    try {
        await navigator.clipboard.writeText(command);
        pushActivity("Command copied", "Chaos playbook command copied to clipboard.");
    } catch (_error) {
        pushActivity("Clipboard blocked", "Copy the chaos playbook command manually.");
    }
}

function installEvents() {
    $("orderForm").addEventListener("submit", submitOrder);
    $("burstButton").addEventListener("click", runBurst);
    $("retryOrderButton").addEventListener("click", retrySelectedOrder);
    $("refreshButton").addEventListener("click", async () => {
        pushActivity("Manual refresh", "Refreshing health, metrics, and order history.");
        await pollPlatform();
    });
    $("resetTemplateButton").addEventListener("click", () => setTemplate("campus"));
    $("priority").addEventListener("input", (event) => {
        $("priorityDisplay").textContent = `${event.target.value} / 10`;
    });
    document.querySelectorAll(".template-chip").forEach((button) => {
        button.addEventListener("click", () => setTemplate(button.dataset.template));
    });
    document.querySelectorAll("[data-copy]").forEach((button) => {
        button.addEventListener("click", () => copyPlaybookCommand(button));
    });
}

async function boot() {
    installEvents();
    setTemplate("campus");
    pushActivity("Dashboard ready", "Polling live platform state every 4 seconds.");
    await pollPlatform();
    window.setInterval(pollPlatform, 4000);
}

document.addEventListener("DOMContentLoaded", boot);
