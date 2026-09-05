"""Production: upload backend + frontend (local vite build + dist upload).

Ubuntu 18.04 sunucuda NVM Node'u eski glibc yüzünden çalışmayabiliyor; bu yüzden
frontend her zaman yerelde `npm run build` ile üretilip dist/ yüklenir.

Kimlik bilgileri ortam değişkenlerinden okunur; repoda parola tutulmaz:

    SENTINEL_DEPLOY_HOST      sunucu adresi (zorunlu)
    SENTINEL_DEPLOY_USER      ssh kullanıcısı (varsayılan: root)
    SENTINEL_DEPLOY_KEY       özel anahtar dosyası (önerilen)
    SENTINEL_DEPLOY_PASSWORD  parola (anahtar yoksa)

Anahtar doğrulaması için ~/.ssh/known_hosts kullanılır. Sunucu ilk kez
ekleniyorsa `ssh-keyscan -H <host> >> ~/.ssh/known_hosts` çalıştırın veya
bilinçli olarak SENTINEL_DEPLOY_TRUST_NEW_HOST=1 verin.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"

BACKEND_FILES = [
    (ROOT / "backend" / "main.py", "/opt/nirvana/backend/main.py"),
    (ROOT / "backend" / "models.py", "/opt/nirvana/backend/models.py"),
    (ROOT / "backend" / "crud.py", "/opt/nirvana/backend/crud.py"),
    (ROOT / "backend" / "schemas.py", "/opt/nirvana/backend/schemas.py"),
    (ROOT / "backend" / "edge_processor.py", "/opt/nirvana/backend/edge_processor.py"),
    (ROOT / "backend" / "simulator.py", "/opt/nirvana/backend/simulator.py"),
    (ROOT / "backend" / "river_learner.py", "/opt/nirvana/backend/river_learner.py"),
    (ROOT / "backend" / "energy_controller.py", "/opt/nirvana/backend/energy_controller.py"),
    (ROOT / "backend" / "rl_agent.py", "/opt/nirvana/backend/rl_agent.py"),
    (ROOT / "backend" / "orbiter_processor.py", "/opt/nirvana/backend/orbiter_processor.py"),
    (ROOT / "backend" / "earth_cloud.py", "/opt/nirvana/backend/earth_cloud.py"),
    (ROOT / "backend" / "rover_ai.py", "/opt/nirvana/backend/rover_ai.py"),
    (
        ROOT / "backend" / "routers" / "anomalies.py",
        "/opt/nirvana/backend/routers/anomalies.py",
    ),
    (
        ROOT / "backend" / "routers" / "nasa.py",
        "/opt/nirvana/backend/routers/nasa.py",
    ),
    (
        ROOT / "backend" / "routers" / "orbiter.py",
        "/opt/nirvana/backend/routers/orbiter.py",
    ),
    (
        ROOT / "backend" / "routers" / "model_updates.py",
        "/opt/nirvana/backend/routers/model_updates.py",
    ),
    (
        ROOT / "backend" / "routers" / "settings.py",
        "/opt/nirvana/backend/routers/settings.py",
    ),
    (
        ROOT / "backend" / "routers" / "websocket.py",
        "/opt/nirvana/backend/routers/websocket.py",
    ),
    (
        ROOT / "backend" / "routers" / "sensor_data.py",
        "/opt/nirvana/backend/routers/sensor_data.py",
    ),
    (
        ROOT / "backend" / "routers" / "uplink_queue.py",
        "/opt/nirvana/backend/routers/uplink_queue.py",
    ),
    (ROOT / "backend" / "requirements.txt", "/opt/nirvana/backend/requirements.txt"),
    (
        ROOT / "backend" / "alembic" / "versions" / "003_channel_ground_truth.py",
        "/opt/nirvana/backend/alembic/versions/003_channel_ground_truth.py",
    ),
    (
        ROOT / "backend" / "alembic" / "versions" / "004_orbiter_novelty.py",
        "/opt/nirvana/backend/alembic/versions/004_orbiter_novelty.py",
    ),
    (
        ROOT / "backend" / "alembic" / "versions" / "005_model_updates.py",
        "/opt/nirvana/backend/alembic/versions/005_model_updates.py",
    ),
]

# Sunucuda kaynak aynası (nginx dist kullanır; yedek / inceleme için)
FRONTEND_SRC_MIRROR = [
    (ROOT / "frontend" / "src" / "App.jsx", "/opt/nirvana/frontend/src/App.jsx"),
    (
        ROOT / "frontend" / "src" / "components" / "LandingPage.jsx",
        "/opt/nirvana/frontend/src/components/LandingPage.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "landing" / "LandingRoverCanvas.jsx",
        "/opt/nirvana/frontend/src/components/landing/LandingRoverCanvas.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "landing" / "MarsSimPanels.jsx",
        "/opt/nirvana/frontend/src/components/landing/MarsSimPanels.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "landing" / "InstrumentStripViz.jsx",
        "/opt/nirvana/frontend/src/components/landing/InstrumentStripViz.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "data" / "landingFlow.js",
        "/opt/nirvana/frontend/src/data/landingFlow.js",
    ),
    (
        ROOT / "frontend" / "src" / "hooks" / "useWebSocket.js",
        "/opt/nirvana/frontend/src/hooks/useWebSocket.js",
    ),
    (
        ROOT / "frontend" / "src" / "hooks" / "useAnomalyData.js",
        "/opt/nirvana/frontend/src/hooks/useAnomalyData.js",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "Dashboard.jsx",
        "/opt/nirvana/frontend/src/components/Dashboard.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "MetricCards.jsx",
        "/opt/nirvana/frontend/src/components/MetricCards.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "AnomalyChart.jsx",
        "/opt/nirvana/frontend/src/components/AnomalyChart.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "AlertCenter.jsx",
        "/opt/nirvana/frontend/src/components/AlertCenter.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "utils" / "formatters.js",
        "/opt/nirvana/frontend/src/utils/formatters.js",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "LiveStreamTable.jsx",
        "/opt/nirvana/frontend/src/components/LiveStreamTable.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "SensorDetail.jsx",
        "/opt/nirvana/frontend/src/components/SensorDetail.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "RoverMap.jsx",
        "/opt/nirvana/frontend/src/components/RoverMap.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "PipelineAnimation.jsx",
        "/opt/nirvana/frontend/src/components/PipelineAnimation.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "OrbiterRelay.jsx",
        "/opt/nirvana/frontend/src/components/OrbiterRelay.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "EarthCloud.jsx",
        "/opt/nirvana/frontend/src/components/EarthCloud.jsx",
    ),
    (
        ROOT / "frontend" / "src" / "components" / "RoverThinking.jsx",
        "/opt/nirvana/frontend/src/components/RoverThinking.jsx",
    ),
]

REMOTE_DIST = "/opt/nirvana/frontend/dist"


def _print_remote(text: str) -> None:
    """Windows konsolu (cp1254) uzak çıktıdaki Unicode yüzünden patlamasın."""
    if not text:
        return
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(text.encode(enc, errors="replace").decode(enc, errors="replace"))


def _connect() -> tuple[paramiko.SSHClient, str]:
    host = os.environ.get("SENTINEL_DEPLOY_HOST", "").strip()
    if not host:
        raise SystemExit(
            "SENTINEL_DEPLOY_HOST tanımlı değil. Örnek:\n"
            '  $env:SENTINEL_DEPLOY_HOST="1.2.3.4"; '
            '$env:SENTINEL_DEPLOY_KEY="$HOME\\.ssh\\id_ed25519"'
        )
    user = os.environ.get("SENTINEL_DEPLOY_USER", "root").strip() or "root"
    key_path = os.environ.get("SENTINEL_DEPLOY_KEY", "").strip()
    password = os.environ.get("SENTINEL_DEPLOY_PASSWORD", "")
    if not key_path and not password:
        raise SystemExit(
            "SENTINEL_DEPLOY_KEY (önerilen) veya SENTINEL_DEPLOY_PASSWORD gerekli."
        )

    c = paramiko.SSHClient()
    c.load_system_host_keys()
    if os.environ.get("SENTINEL_DEPLOY_TRUST_NEW_HOST") == "1":
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        c.set_missing_host_key_policy(paramiko.RejectPolicy())

    kwargs: dict = {"username": user, "timeout": 45}
    if key_path:
        kwargs["key_filename"] = key_path
    else:
        kwargs["password"] = password
    c.connect(host, **kwargs)
    return c, host


def _run_local_build() -> None:
    if os.name == "nt":
        subprocess.run("npm run build", cwd=str(FRONTEND), shell=True, check=True)
    else:
        subprocess.run(["npm", "run", "build"], cwd=str(FRONTEND), check=True)


def _sftp_mkdirs(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = [p for p in remote_dir.split("/") if p]
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            try:
                sftp.mkdir(cur)
            except OSError:
                pass


def _ensure_systemd_env_file(client: paramiko.SSHClient) -> None:
    """NASA_API_KEY vb. için /opt/nirvana/backend/.env okunabilsin."""
    script = r"""python3 << 'PY'
from pathlib import Path
p = Path("/etc/systemd/system/nirvana.service")
if not p.is_file():
    raise SystemExit("nirvana.service yok")
t = p.read_text()
needle = "EnvironmentFile=-/opt/nirvana/backend/.env"
if needle in t:
    print("systemd: EnvironmentFile zaten var")
    raise SystemExit(0)
if "[Service]" not in t:
    raise SystemExit("nirvana.service [Service] yok")
t = t.replace("[Service]\n", "[Service]\n" + needle + "\n", 1)
p.write_text(t)
print("systemd: EnvironmentFile eklendi")
PY"""
    _, stdout, stderr = client.exec_command(script, timeout=30)
    code = stdout.channel.recv_exit_status()
    out = (stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip()
    if out:
        _print_remote(out)
    if code != 0:
        raise RuntimeError("systemd EnvironmentFile patch başarısız")


def _upload_dist(sftp: paramiko.SFTPClient) -> None:
    for root, _dirs, files in os.walk(DIST):
        rel = Path(root).relative_to(DIST)
        for f in files:
            lp = Path(root) / f
            if str(rel) == ".":
                rp = f"{REMOTE_DIST}/{f}"
            else:
                rp = f"{REMOTE_DIST}/{rel.as_posix()}/{f}"
            parent = str(Path(rp).parent).replace("\\", "/")
            _sftp_mkdirs(sftp, parent)
            sftp.put(str(lp), rp)
            print(f"OK dist {lp.relative_to(ROOT)} -> {rp}")


def main() -> None:
    print("Local: npm run build …")
    _run_local_build()

    c, host = _connect()
    sftp = c.open_sftp()

    for local, rpath in BACKEND_FILES:
        if not local.is_file():
            raise FileNotFoundError(local)
        sftp.put(str(local), rpath)
        print(f"OK {local.relative_to(ROOT)} -> {rpath}")

    for local, rpath in FRONTEND_SRC_MIRROR:
        if not local.is_file():
            raise FileNotFoundError(local)
        parent = str(Path(rpath).parent).replace("\\", "/")
        if parent and parent != ".":
            _sftp_mkdirs(sftp, parent)
        sftp.put(str(local), rpath)
        print(f"OK {local.relative_to(ROOT)} -> {rpath}")

    _upload_dist(sftp)

    env_local = ROOT / "backend" / ".env"
    if env_local.is_file():
        sftp.put(str(env_local), "/opt/nirvana/backend/.env")
        print(f"OK {env_local.relative_to(ROOT)} -> /opt/nirvana/backend/.env")

    sftp.close()

    _ensure_systemd_env_file(c)
    _, stdout, _ = c.exec_command("systemctl daemon-reload", timeout=30)
    stdout.channel.recv_exit_status()

    _, stdout, stderr = c.exec_command(
        """bash -lc '
PIP=""
if [ -x /opt/nirvana/backend/venv/bin/pip ]; then PIP=/opt/nirvana/backend/venv/bin/pip
elif [ -x /opt/miniconda/bin/pip ]; then PIP=/opt/miniconda/bin/pip
fi
if [ -n "$PIP" ]; then cd /opt/nirvana/backend && \
  "$PIP" install -U pip setuptools wheel && \
  "$PIP" install -r requirements.txt --prefer-binary 2>&1
else echo "pip bulunamadı (venv veya miniconda)"; exit 1
fi
'""",
        timeout=300,
    )
    pip_out = (stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip()
    if pip_out:
        _print_remote(pip_out[-2500:])

    _, stdout, stderr = c.exec_command(
        """bash -lc '
ALB=""
if [ -x /opt/nirvana/backend/venv/bin/alembic ]; then ALB=/opt/nirvana/backend/venv/bin/alembic
elif [ -x /opt/miniconda/bin/alembic ]; then ALB=/opt/miniconda/bin/alembic
fi
if [ -n "$ALB" ]; then cd /opt/nirvana/backend && "$ALB" upgrade head 2>&1
else echo "alembic atlandı (yok)"; exit 0
fi
'""",
        timeout=120,
    )
    mig = (stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip()
    if mig:
        _print_remote(mig[-2000:])

    _, stdout, _ = c.exec_command("systemctl restart nirvana", timeout=90)
    stdout.channel.recv_exit_status()
    time.sleep(2)
    _, stdout, stderr = c.exec_command(
        "systemctl is-active nirvana && curl -s http://127.0.0.1:8000/health", timeout=30
    )
    _print_remote((stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip())

    _, stdout, _ = c.exec_command("systemctl restart nginx", timeout=60)
    stdout.channel.recv_exit_status()
    c.close()
    print(f"Done. http://{host}")


if __name__ == "__main__":
    main()
