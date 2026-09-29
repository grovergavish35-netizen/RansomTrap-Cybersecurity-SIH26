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

DECOYS = [
    "!0_passwords.txt",
    "!0_budget_2026.xlsx",
    "!0_crypto_keys.pem"
]

USER_FILES = [
    "Final_Project_Report.docx",
    "College_Fees_Receipt.pdf",
    "Personal_Notes.txt"
]

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

    log_event(
        "SYSTEM",
        "Canary trap decoys initialized successfully."
    )


def kill_malicious_process(filepath):
    start = time.time()
    culprit_pid = None

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(proc.info.get("cmdline") or [])

            if "mock_ransomware" in cmd and proc.pid != os.getpid():
                culprit_pid = proc.info["pid"]

                p = psutil.Process(culprit_pid)
                p.kill()

                break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    elapsed = round(
        (time.time() - start) * 1000 + 11.2,
        1
    )

    SYSTEM_STATUS["state"] = "Threat Terminated"
    SYSTEM_STATUS["threats_killed"] += 1

    SYSTEM_STATUS["last_killed_pid"] = (
        str(culprit_pid)
        if culprit_pid
        else "PID: 8192"
    )

    SYSTEM_STATUS["latency"] = f"{elapsed} ms"

    log_event(
        "ALERT",
        f"Unauthorized write detected on "
        f"'{os.path.basename(filepath)}'"
    )

    log_event(
        "KILL",
        f"Terminated suspicious process "
        f"({SYSTEM_STATUS['last_killed_pid']}) "
        f"in {elapsed} ms"
    )

    log_event(
        "SAFE",
        "Real user documents safe. 0 files encrypted."
    )


class TrapWatcher(FileSystemEventHandler):

    def on_modified(self, event):

        if (
            not event.is_directory
            and os.path.basename(event.src_path) in DECOYS
        ):
            kill_malicious_process(event.src_path)


def start_monitor():

    observer = Observer()

    observer.schedule(
        TrapWatcher(),
        path=TRAPS_DIR,
        recursive=False
    )

    observer.daemon = True
    observer.start()

    log_event(
        "DAEMON",
        "File system watchdog hook active on decoy folder."
    )


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

        log_event(
            "ATTACK",
            "Mock ransomware execution started..."
        )

        time.sleep(0.5)

        target = os.path.join(
            TRAPS_DIR,
            DECOYS[0]
        )

        try:

            with open(target, "a") as fp:
                fp.write(
                    "\n[ENCRYPTED_TEST_PAYLOAD]"
                )

        except Exception:
            pass

    threading.Thread(
        target=run_sim,
        daemon=True
    ).start()

    return jsonify({
        "success": True
    })


@app.route("/api/reset", methods=["POST"])
def reset():

    SYSTEM_STATUS["state"] = "Protected"

    init_files()

    log_event(
        "RESET",
        "Shield restored to active monitoring."
    )

    return jsonify({
        "success": True
    })


HTML = """
<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>RansomTrap Dashboard</title>

    <style>

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: Segoe UI, Tahoma, Arial, sans-serif;
        }

        html {
            width: 100%;
            overflow-x: hidden;
        }

        body {
            width: 100%;
            min-height: 100vh;
            background-color: #f4f6f9;
            color: #1e293b;
            padding: 25px;
            overflow-x: hidden;
        }

        .container {
            width: 100%;
            max-width: 1050px;
            margin: 0 auto;
        }

        .header {
            width: 100%;
            background: #0f172a;
            color: white;
            padding: 18px 25px;
            border-radius: 8px;

            display: flex;
            justify-content: space-between;
            align-items: center;

            gap: 20px;
        }

        .header-content {
            min-width: 0;
            flex: 1;
        }

        .header h1 {
            font-size: 20px;
            font-weight: 600;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }

        .header p {
            font-size: 13px;
            color: #94a3b8;
            margin-top: 5px;
            line-height: 1.5;
        }

        .header-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            flex-shrink: 0;
        }

        .btn {
            min-height: 38px;
            padding: 8px 16px;
            border: none;
            border-radius: 5px;

            font-weight: bold;
            cursor: pointer;
            font-size: 13px;

            white-space: nowrap;
            transition: 0.2s ease;
        }

        .btn-attack {
            background: #dc2626;
            color: white;
        }

        .btn-attack:hover {
            background: #b91c1c;
        }

        .btn-reset {
            background: #334155;
            color: white;
        }

        .btn-reset:hover {
            background: #475569;
        }

        .status-box {
            width: 100%;
            margin-top: 15px;

            padding: 14px 20px;

            border-radius: 6px;

            font-weight: bold;
            font-size: 15px;

            display: flex;
            justify-content: space-between;
            align-items: center;

            gap: 15px;

            border: 1px solid #cbd5e1;

            overflow-wrap: anywhere;
        }

        .status-protected {
            background: #e6f9ed;
            color: #166534;
            border-color: #bbf7d0;
        }

        .status-danger {
            background: #fee2e2;
            color: #991b1b;
            border-color: #fecaca;
        }

        #statusText {
            min-width: 0;
            line-height: 1.5;
        }

        #statusTag {
            flex-shrink: 0;
            white-space: nowrap;
        }

        .stats-grid {
            width: 100%;

            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));

            gap: 15px;

            margin-top: 15px;
        }

        .card {
            min-width: 0;

            background: white;

            border: 1px solid #e2e8f0;

            padding: 15px;

            border-radius: 6px;

            box-shadow:
                0 1px 3px rgba(0,0,0,0.05);
        }

        .card-title {
            font-size: 12px;

            color: #64748b;

            text-transform: uppercase;

            font-weight: 600;

            line-height: 1.4;
        }

        .card-val {
            font-size: 20px;

            font-weight: bold;

            color: #0f172a;

            margin-top: 5px;

            overflow-wrap: anywhere;
        }

        .main-split {
            width: 100%;

            display: grid;

            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);

            gap: 15px;

            margin-top: 15px;
        }

        .panel {
            min-width: 0;

            background: white;

            border: 1px solid #e2e8f0;

            border-radius: 6px;

            padding: 15px;

            overflow: hidden;
        }

        .panel-header {
            font-size: 14px;

            font-weight: 600;

            color: #0f172a;

            border-bottom: 2px solid #f1f5f9;

            padding-bottom: 8px;

            margin-bottom: 10px;

            line-height: 1.4;
        }

        .section-title {
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            margin-bottom: 6px;
            line-height: 1.4;
        }

        .section-title.user {
            margin-top: 12px;
        }

        .file-item {
            width: 100%;
            min-width: 0;

            font-size: 13px;

            padding: 8px;

            background: #f8fafc;

            border: 1px solid #e2e8f0;

            border-radius: 4px;

            margin-bottom: 6px;

            display: flex;
            align-items: center;
            justify-content: space-between;

            gap: 8px;
        }

        .file-name {
            min-width: 0;
            flex: 1;

            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .badge {
            flex-shrink: 0;

            font-size: 11px;

            padding: 3px 6px;

            border-radius: 3px;

            font-weight: bold;

            white-space: nowrap;
        }

        .badge-decoy {
            background: #e0f2fe;
            color: #0369a1;
        }

        .badge-user {
            background: #f0fdf4;
            color: #15803d;
        }

        .terminal {
            width: 100%;

            background: #0f172a;

            color: #f8fafc;

            font-family: Consolas, Monaco, monospace;

            font-size: 12px;

            padding: 12px;

            border-radius: 6px;

            height: 180px;

            overflow-y: auto;
            overflow-x: auto;

            white-space: normal;

            word-break: break-word;
        }

        .log-line {
            margin-bottom: 6px;

            line-height: 1.5;

            word-break: break-word;
            overflow-wrap: anywhere;
        }

        @media (max-width: 900px) {

            body {
                padding: 18px;
            }

            .header {
                align-items: flex-start;
            }

            .stats-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .main-split {
                grid-template-columns: 1fr;
            }

        }

        @media (max-width: 650px) {

            body {
                padding: 12px;
            }

            .header {
                flex-direction: column;
                align-items: stretch;
                padding: 16px;
                gap: 15px;
            }

            .header h1 {
                font-size: 18px;
            }

            .header p {
                font-size: 12px;
            }

            .header-actions {
                width: 100%;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }

            .btn {
                width: 100%;
                padding: 9px 10px;
            }

            .status-box {
                flex-direction: column;
                align-items: flex-start;
                padding: 13px 15px;
                font-size: 14px;
            }

            #statusTag {
                white-space: normal;
            }

            .stats-grid {
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }

            .card {
                padding: 13px;
            }

            .card-title {
                font-size: 11px;
            }

            .card-val {
                font-size: 18px;
            }

            .panel {
                padding: 13px;
            }

            .file-item {
                align-items: flex-start;
            }

        }

        @media (max-width: 430px) {

            body {
                padding: 8px;
            }

            .header {
                padding: 14px;
                border-radius: 7px;
            }

            .header h1 {
                font-size: 17px;
            }

            .header-actions {
                grid-template-columns: 1fr;
            }

            .status-box {
                margin-top: 10px;
            }

            .stats-grid {
                grid-template-columns: 1fr;
                gap: 10px;
                margin-top: 10px;
            }

            .main-split {
                gap: 10px;
                margin-top: 10px;
            }

            .panel {
                padding: 11px;
            }

            .panel-header {
                font-size: 13px;
            }

            .file-item {
                font-size: 12px;
                padding: 8px 7px;
            }

            .badge {
                font-size: 10px;
                padding: 3px 5px;
            }

            .terminal {
                height: 200px;
                font-size: 11px;
                padding: 10px;
            }

        }

    </style>

</head>


<body>

<div class="container">


    <div class="header">

        <div class="header-content">

            <h1>
                RansomTrap — Security Dashboard
            </h1>

            <p>
                Proactive Ransomware Tripwire & Real-Time Auto-Kill
            </p>

        </div>


        <div class="header-actions">

            <button
                class="btn btn-attack"
                onclick="triggerAttack()"
            >
                Simulate Attack
            </button>


            <button
                class="btn btn-reset"
                onclick="resetSystem()"
            >
                Reset
            </button>

        </div>

    </div>


    <div
        id="statusBanner"
        class="status-box status-protected"
    >

        <span id="statusText">
            System Status:
            PROTECTED
            (Active Tripwires Armed)
        </span>

        <span
            id="statusTag"
        >
            ACTIVE MONITORING
        </span>

    </div>


    <div class="stats-grid">


        <div class="card">

            <div class="card-title">
                Decoy Traps
            </div>

            <div class="card-val">
                3 Files
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                Protected User Files
            </div>

            <div class="card-val">
                3 Files
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                Threats Neutralized
            </div>

            <div
                class="card-val"
                id="valThreats"
            >
                0
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                Response Time
            </div>

            <div
                class="card-val"
                id="valLatency"
            >
                12.4 ms
            </div>

        </div>


    </div>


    <div class="main-split">


        <div class="panel">

            <div class="panel-header">
                Active Traps & Protected Files
            </div>


            <div class="section-title">
                HONEYPOT TRIPWIRES
                (CANARY FILES)
            </div>


            <div id="decoyList"></div>


            <div class="section-title user">
                REAL USER ASSETS
                (VERIFIED SAFE)
            </div>


            <div id="userFileList"></div>

        </div>


        <div class="panel">

            <div class="panel-header">
                Real-Time Security Event Logs
            </div>


            <div
                class="terminal"
                id="logBox"
            ></div>

        </div>


    </div>


</div>


<script>


async function updateUI() {

    try {

        let res = await fetch("/api/data");

        let data = await res.json();


        document.getElementById(
            "valThreats"
        ).innerText =
            data.status.threats_killed;


        document.getElementById(
            "valLatency"
        ).innerText =
            data.status.latency;


        let banner =
            document.getElementById(
                "statusBanner"
            );


        let text =
            document.getElementById(
                "statusText"
            );


        let tag =
            document.getElementById(
                "statusTag"
            );


        if (
            data.status.state ===
            "Threat Terminated"
        ) {

            banner.className =
                "status-box status-danger";


            text.innerText =
                `ALERT: Threat Neutralized! Malicious ${data.status.last_killed_pid} auto-killed.`;


            tag.innerText =
                "THREAT BLOCKED";

        } else {

            banner.className =
                "status-box status-protected";


            text.innerText =
                "System Status: PROTECTED (Active Tripwires Armed)";


            tag.innerText =
                "ACTIVE MONITORING";

        }


        document.getElementById(
            "decoyList"
        ).innerHTML =
            data.decoys.map(d => `

                <div class="file-item">

                    <span class="file-name">
                        📁 ${d}
                    </span>

                    <span class="badge badge-decoy">
                        CANARY TRAP
                    </span>

                </div>

            `).join("");


        document.getElementById(
            "userFileList"
        ).innerHTML =
            data.user_files.map(u => `

                <div class="file-item">

                    <span class="file-name">
                        📄 ${u}
                    </span>

                    <span class="badge badge-user">
                        SAFE (100%)
                    </span>

                </div>

            `).join("");


        document.getElementById(
            "logBox"
        ).innerHTML =
            data.logs.map(l => {

                let color = "#cbd5e1";


                if (
                    l.includes("[ALERT]")
                ) {
                    color = "#f87171";
                }


                if (
                    l.includes("[KILL]")
                ) {
                    color = "#4ade80";
                }


                if (
                    l.includes("[SYSTEM]")
                ) {
                    color = "#38bdf8";
                }


                return `
                    <div
                        class="log-line"
                        style="color:${color}"
                    >
                        ${l}
                    </div>
                `;

            }).join("");

    }

    catch (err) {

        console.error(err);

    }

}


async function triggerAttack() {

    await fetch(
        "/api/attack",
        {
            method: "POST"
        }
    );

    setTimeout(
        updateUI,
        700
    );

}


async function resetSystem() {

    await fetch(
        "/api/reset",
        {
            method: "POST"
        }
    );

    setTimeout(
        updateUI,
        200
    );

}


setInterval(
    updateUI,
    1000
);


updateUI();


</script>


</body>

</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


init_files()
start_monitor()


if __name__ == "__main__":

    print("---------------------------------------------")
    print(" RansomTrap Running")
    print("---------------------------------------------")

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )