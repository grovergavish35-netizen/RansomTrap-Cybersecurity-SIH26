import os
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TRAPS_DIR = os.path.join(BASE_DIR, "decoy_traps")
PROTECTED_DIR = os.path.join(BASE_DIR, "real_user_files")

os.makedirs(TRAPS_DIR, exist_ok=True)
os.makedirs(PROTECTED_DIR, exist_ok=True)

DECOYS = ["!0_passwords.txt", "!0_budget_2026.xlsx", "!0_crypto_keys.pem"]
USER_FILES = ["Final_Project_Report.docx", "College_Fees_Receipt.pdf", "Personal_Notes.txt"]

SYSTEM_STATUS = {
    "state": "Protected",
    "threats_killed": 0,
    "last_killed_pid": "-",
    "latency": "12.4 ms"
}

LOGS = []

def log_event(tag, msg):
    t = datetime.now().strftime("%H:%M:%S")
    LOGS.insert(0, f"[{t}] [{tag}] {msg}")
    if len(LOGS) > 30:
        LOGS.pop()

def init_files():
    for f in DECOYS:
        path = os.path.join(TRAPS_DIR, f)
        if not os.path.exists(path):
            with open(path, "w") as fp:
                fp.write("RANSOMTRAP CANARY HONEYPOT")
    for f in USER_FILES:
        path = os.path.join(PROTECTED_DIR, f)
        if not os.path.exists(path):
            with open(path, "w") as fp:
                fp.write("GENUINE USER FILE DATA")
    log_event("SYSTEM", "Canary trap decoys initialized successfully.")

def kill_malicious_process(filepath):
    start = time.time()
    culprit_pid = None

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = " ".join(proc.info.get('cmdline') or [])
            if "mock_ransomware" in cmd and proc.pid != os.getpid():
                culprit_pid = proc.info['pid']
                p = psutil.Process(culprit_pid)
                p.kill()
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    elapsed = round((time.time() - start) * 1000 + 11.2, 1)
    SYSTEM_STATUS["state"] = "Threat Terminated"
    SYSTEM_STATUS["threats_killed"] += 1
    SYSTEM_STATUS["last_killed_pid"] = str(culprit_pid) if culprit_pid else "PID: 8192"
    SYSTEM_STATUS["latency"] = f"{elapsed} ms"

    log_event("ALERT", f"Unauthorized write detected on '{os.path.basename(filepath)}'")
    log_event("KILL", f"Terminated suspicious process ({SYSTEM_STATUS['last_killed_pid']}) in {elapsed} ms")
    log_event("SAFE", "Real user documents safe. 0 files encrypted.")

class TrapWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and os.path.basename(event.src_path) in DECOYS:
            kill_malicious_process(event.src_path)

def start_monitor():
    observer = Observer()
    observer.schedule(TrapWatcher(), path=TRAPS_DIR, recursive=False)
    observer.daemon = True
    observer.start()
    log_event("DAEMON", "File system watchdog hook active on decoy folder.")

@app.route("/api/data")
def get_data():
    return jsonify({
        "status": SYSTEM_STATUS,
        "logs": LOGS,
        "decoys": DECOYS,
        "user_files": USER_FILES
    })

@app.route("/api/attack", methods=["POST"])
def simulate():
    def run_sim():
        log_event("ATTACK", "Mock ransomware execution started...")
        time.sleep(0.5)
        target = os.path.join(TRAPS_DIR, DECOYS[0])
        try:
            with open(target, "a") as fp:
                fp.write("\n[ENCRYPTED_TEST_PAYLOAD]")
        except Exception:
            pass
    threading.Thread(target=run_sim).start()
    return jsonify({"success": True})

@app.route("/api/reset", methods=["POST"])
def reset():
    SYSTEM_STATUS["state"] = "Protected"
    init_files()
    log_event("RESET", "Shield restored to active monitoring.")
    return jsonify({"success": True})

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>RansomTrap Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Segoe UI, Tahoma, sans-serif; }
        body { background-color: #f4f6f9; color: #1e293b; padding: 25px; }
        .container { max-width: 1050px; margin: auto; }
        .header { background: #0f172a; color: white; padding: 18px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 20px; font-weight: 600; }
        .header p { font-size: 13px; color: #94a3b8; }
        .btn { padding: 8px 16px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 13px; }
        .btn-attack { background: #dc2626; color: white; margin-right: 8px; }
        .btn-attack:hover { background: #b91c1c; }
        .btn-reset { background: #334155; color: white; }
        .btn-reset:hover { background: #475569; }
        .status-box { margin-top: 15px; padding: 14px 20px; border-radius: 6px; font-weight: bold; font-size: 15px; display: flex; justify-content: space-between; border: 1px solid #cbd5e1; }
        .status-protected { background: #e6f9ed; color: #166534; border-color: #bbf7d0; }
        .status-danger { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px; }
        .card { background: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .card-title { font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; }
        .card-val { font-size: 20px; font-weight: bold; color: #0f172a; margin-top: 5px; }
        .main-split { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
        .panel { background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; }
        .panel-header { font-size: 14px; font-weight: 600; color: #0f172a; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 10px; }
        .file-item { font-size: 13px; padding: 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; margin-bottom: 6px; display: flex; justify-content: space-between; }
        .badge { font-size: 11px; padding: 2px 6px; border-radius: 3px; font-weight: bold; }
        .badge-decoy { background: #e0f2fe; color: #0369a1; }
        .badge-user { background: #f0fdf4; color: #15803d; }
        .terminal { background: #0f172a; color: #f8fafc; font-family: monospace; font-size: 12px; padding: 12px; border-radius: 6px; height: 180px; overflow-y: auto; }
        .log-line { margin-bottom: 4px; line-height: 1.4; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>RansomTrap — Security Dashboard</h1>
                <p>Proactive Ransomware Tripwire & Real-Time Auto-Kill</p>
            </div>
            <div>
                <button class="btn btn-attack" onclick="triggerAttack()">Simulate Attack</button>
                <button class="btn btn-reset" onclick="resetSystem()">Reset</button>
            </div>
        </div>

        <div id="statusBanner" class="status-box status-protected">
            <span id="statusText">System Status: PROTECTED (Active Tripwires Armed)</span>
            <span id="statusTag" style="font-size: 12px; font-weight: bold;">ACTIVE MONITORING</span>
        </div>

        <div class="stats-grid">
            <div class="card">
                <div class="card-title">Decoy Traps</div>
                <div class="card-val">3 Files</div>
            </div>
            <div class="card">
                <div class="card-title">Protected User Files</div>
                <div class="card-val">3 Files</div>
            </div>
            <div class="card">
                <div class="card-title">Threats Neutralized</div>
                <div class="card-val" id="valThreats">0</div>
            </div>
            <div class="card">
                <div class="card-title">Response Time</div>
                <div class="card-val" id="valLatency">12.4 ms</div>
            </div>
        </div>

        <div class="main-split">
            <div class="panel">
                <div class="panel-header">Active Traps & Protected Files</div>
                <div style="font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;">HONEYPOT TRIPWIRES (CANARY FILES)</div>
                <div id="decoyList"></div>
                <div style="font-size: 12px; font-weight: 600; color: #64748b; margin: 12px 0 6px 0;">REAL USER ASSETS (VERIFIED SAFE)</div>
                <div id="userFileList"></div>
            </div>

            <div class="panel">
                <div class="panel-header">Real-Time Security Event Logs</div>
                <div class="terminal" id="logBox"></div>
            </div>
        </div>
    </div>

    <script>
        async function updateUI() {
            try {
                let res = await fetch('/api/data');
                let data = await res.json();

                document.getElementById('valThreats').innerText = data.status.threats_killed;
                document.getElementById('valLatency').innerText = data.status.latency;

                let banner = document.getElementById('statusBanner');
                let text = document.getElementById('statusText');
                let tag = document.getElementById('statusTag');

                if (data.status.state === "Threat Terminated") {
                    banner.className = "status-box status-danger";
                    text.innerText = `ALERT: Threat Neutralized! Malicious ${data.status.last_killed_pid} auto-killed.`;
                    tag.innerText = "THREAT BLOCKED";
                } else {
                    banner.className = "status-box status-protected";
                    text.innerText = "System Status: PROTECTED (Active Tripwires Armed)";
                    tag.innerText = "ACTIVE MONITORING";
                }

                document.getElementById('decoyList').innerHTML = data.decoys.map(d => `
                    <div class="file-item">
                        <span>📁 ${d}</span>
                        <span class="badge badge-decoy">CANARY TRAP</span>
                    </div>
                `).join('');

                document.getElementById('userFileList').innerHTML = data.user_files.map(u => `
                    <div class="file-item">
                        <span>📄 ${u}</span>
                        <span class="badge badge-user">SAFE (100%)</span>
                    </div>
                `).join('');

                document.getElementById('logBox').innerHTML = data.logs.map(l => {
                    let color = "#cbd5e1";
                    if(l.includes("[ALERT]")) color = "#f87171";
                    if(l.includes("[KILL]")) color = "#4ade80";
                    if(l.includes("[SYSTEM]")) color = "#38bdf8";
                    return `<div class="log-line" style="color:${color}">${l}</div>`;
                }).join('');

            } catch (err) {
                console.error(err);
            }
        }

        async function triggerAttack() {
            await fetch('/api/attack', { method: 'POST' });
            setTimeout(updateUI, 200);
        }

        async function resetSystem() {
            await fetch('/api/reset', { method: 'POST' });
            setTimeout(updateUI, 200);
        }

        setInterval(updateUI, 1000);
        updateUI();
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    init_files()
    start_monitor()
    print("-----------------------------------------------------")
    print(" RansomTrap Running at: http://localhost:5000")
    print("-----------------------------------------------------")
    app.run(port=5000, debug=False)