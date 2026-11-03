const API_TOKEN = "beman_kar_bedid";


async function apiRequest(endpoint, method = "GET", body = null) {
    const options = {
        method,
        headers: {
            "Authorization": API_TOKEN,
            "Content-Type": "application/json"
        }
    };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(endpoint, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Khataye ertebat ba server");
    }
    return data;
}

function showMessage(elementId, text, color) {
    const el = document.getElementById(elementId);
    el.innerText = text;
    el.style.color = color;
}


async function updateTelemetry() {
    const badge = document.getElementById("live-badge");
    const btnStart = document.getElementById("btn-start");
    const btnStop = document.getElementById("btn-stop");

    try {
        const data = await apiRequest("/api/telemetry");
        
        badge.innerText = data.online ? "وضعیت: روشن (Online)" : "وضعیت: خاموش (Offline)";
        badge.style.backgroundColor = data.online ? "#059669" : "#dc2626";

        btnStart.disabled = data.online;
        btnStop.disabled = !data.online;

        document.getElementById("res-cpu").innerText = `${data.cpu}%`;
        document.getElementById("res-ram").innerText = `${data.ram}%`;
        document.getElementById("res-port").innerText = data.port;
    } catch (error) {
        badge.innerText = "عدم ارتباط با سرور";
        badge.style.backgroundColor = "#475569";
    }
}

async function handleServerControl(action) {
    showMessage("action-msg", "در حال ارسال فرمان...", "#f59e0b");
    try {
        const result = await apiRequest(`/api/${action}`, "POST");
        showMessage("action-msg", result.message, "#10b981");
        setTimeout(updateTelemetry, 1000);
    } catch (error) {
        showMessage("action-msg", `خطا: ${error.message}`, "#ef4444");
    }
}

async function loadSettings() {
    try {
        const data = await apiRequest("/api/settings");
        document.getElementById("set-name").value = data.name;
        document.getElementById("set-world").value = data.world;
        document.getElementById("set-password").value = data.password;
        document.getElementById("set-port").value = data.port || 2456;
        document.getElementById("set-public").checked = data.public === 1;
        document.getElementById("set-crossplay").checked = data.crossplay;
    } catch (error) {
        console.error("Settings load error:", error.message);
    }
}

// 6. Zakhireye tanzimate jadid
async function handleSaveSettings(event) {
    event.preventDefault();
    showMessage("settings-msg", "در حال ذخیره...", "#f59e0b");

    const payload = {
        name: document.getElementById("set-name").value.trim(),
        world: document.getElementById("set-world").value.trim(),
        password: document.getElementById("set-password").value,
        port: parseInt(document.getElementById("set-port").value, 10) || 2456,
        public: document.getElementById("set-public").checked ? 1 : 0,
        crossplay: document.getElementById("set-crossplay").checked
    };

    try {
        const result = await apiRequest("/api/settings", "POST", payload);
        showMessage("settings-msg", result.message, "#10b981");
        updateTelemetry();
    } catch (error) {
        showMessage("settings-msg", `خطا: ${error.message}`, "#ef4444");
    }
}

// 7. Etesale Event-ha va shorooe barname
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btn-start").addEventListener("click", () => handleServerControl("start"));
    document.getElementById("btn-stop").addEventListener("click", () => handleServerControl("stop"));
    document.getElementById("settings-form").addEventListener("submit", handleSaveSettings);

    loadSettings();
    updateTelemetry();
    setInterval(updateTelemetry, 3000);
});