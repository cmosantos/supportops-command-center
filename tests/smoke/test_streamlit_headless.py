# ruff: noqa: E501, S603
"""Bounded real-process Streamlit health smoke."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


def test_real_streamlit_headless_health(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    app_path = project_root / "src/supportops/streamlit_app.py"
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = os.environ.copy()
    env["SUPPORTOPS_DB_PATH"] = str(tmp_path / "smoke.db")
    env["SUPPORTOPS_EXPORT_ROOT"] = str(tmp_path / "exports")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
    ]
    process = subprocess.Popen(
        command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )  # noqa: S603
    try:
        for _ in range(30):
            if process.poll() is not None:
                raise AssertionError("Streamlit exited before health became ready")
            try:
                with urlopen(
                    f"http://127.0.0.1:{port}/_stcore/health", timeout=1
                ) as response:  # noqa: S310
                    if response.status == 200:
                        with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as root:  # noqa: S310
                            assert root.status == 200
                            assert b"streamlit" in root.read().lower()
                        break
            except OSError:
                time.sleep(0.2)
        else:
            raise AssertionError("Streamlit health did not become ready")
        assert process.poll() is None
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        logs = process.stdout.read() if process.stdout else ""
        assert "Traceback" not in logs
        assert "secret" not in logs.casefold()
        assert str(project_root) not in logs
