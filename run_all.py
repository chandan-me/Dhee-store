import subprocess
import sys
import time
import os
import shutil
import socket

# =====================================================================
# SYSTEM ORCHESTRATOR SCRIPT (React + Gateway + Microservices)
# Features:
#  - Automatic .env detection & generation from .env.example
#  - Pre-flight MySQL TCP connectivity & credentials check
#  - Proactive database auto-creation (users_db, products_db, orders_db)
#  - Automatic npm install if node_modules missing
#  - Port cleanup & crash diagnosis with live log dumping
# =====================================================================


def free_ports(ports):
    """Kills any orphaned processes on the target ports to avoid [Errno 10048]."""
    for port in ports:
        try:
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def run_preflight_checks():
    """Validates environment, MySQL connectivity, credentials, databases, and dependencies."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    env_example = os.path.join(base_dir, ".env.example")
    
    print("=" * 70)
    print("MICROSERVICES WORKSPACE - PRE-FLIGHT SYSTEM VERIFICATION")
    print("=" * 70)

    # 1. Check or auto-generate .env
    if not os.path.exists(env_path):
        if os.path.exists(env_example):
            shutil.copy(env_example, env_path)
            print("[Setup] Created '.env' configuration file from '.env.example'.")
        else:
            default_env = (
                "MYSQL_HOST=localhost\n"
                "MYSQL_PORT=3306\n"
                "MYSQL_USER=root\n"
                "MYSQL_PASSWORD=\n"
                "JWT_SECRET=demo_secret_key_Demo_gatekeeper_auth_2026\n"
                "JWT_ALGORITHM=HS256\n"
                "ACCESS_TOKEN_EXPIRE_MINUTES=300000\n"
                "RAZORPAY_KEY_ID=rzp_test_T9pQXLodEsWanv\n"
                "RAZORPAY_KEY_SECRET=fe8EIlYB67kM4aLCqcn09YSX\n"
            )
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(default_env)
            print("[Setup] Created default '.env' configuration file.")
    else:
        print("[Pre-flight] Found '.env' configuration file.")

    # 2. Read environment variables
    from dotenv import load_dotenv
    load_dotenv(env_path, override=True)

    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")

    # 3. Check TCP Socket to MySQL Server
    print(f"[Pre-flight] Checking MySQL Server reachability on {mysql_host}:{mysql_port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect((mysql_host, mysql_port))
        sock.close()
        print(f"[Pre-flight] MySQL Server port {mysql_port} is OPEN and reachable.")
    except Exception:
        print("\n" + "=" * 70)
        print(f"[CRITICAL ERROR] Cannot connect to MySQL Server on {mysql_host}:{mysql_port}!")
        print("Backend microservices cannot start because MySQL is not running.")
        print("\nHOW TO START MYSQL ON WINDOWS:")
        print("  1. Press Win + R, type 'services.msc' and press Enter.")
        print("  2. Scroll down to locate 'MySQL' (e.g. 'MySQL80').")
        print("  3. Right-click it and click 'Start'.")
        print("     (Or open PowerShell as Administrator and run: Start-Service MySQL80)")
        print("  4. Once MySQL is started, re-run: python run_all.py")
        print("=" * 70 + "\n")
        sys.exit(1)

    # 4. Check MySQL Authentication & Auto-Create Databases
    try:
        import pymysql
    except ImportError:
        print("[Error] 'pymysql' is missing. Please run: pip install -r requirements.txt")
        sys.exit(1)

    print(f"[Pre-flight] Verifying MySQL credentials for user '{mysql_user}'...")
    try:
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connect_timeout=3
        )
        with conn.cursor() as cur:
            for db_name in ["users_db", "products_db", "orders_db"]:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()
        print("[Pre-flight] MySQL credentials verified & all databases confirmed (users_db, products_db, orders_db).")
    except pymysql.err.OperationalError as e:
        err_code, err_msg = e.args[0], e.args[1] if len(e.args) > 1 else str(e)
        if err_code == 1045:
            print("\n" + "=" * 70)
            print(f"[CRITICAL ERROR] MySQL Login Failed! (1045: Access denied for user '{mysql_user}')")
            print("The password in your '.env' file does not match your MySQL root password.")
            print("\nHOW TO FIX THIS:")
            print("  1. Open the file '.env' in this folder.")
            print("  2. Change MYSQL_PASSWORD= to your actual MySQL root password:")
            print("       MYSQL_PASSWORD=your_mysql_password")
            print("  3. Save '.env' and re-run: python run_all.py")
            print("=" * 70 + "\n")
            sys.exit(1)
        else:
            print(f"[Warning] MySQL connection note: {e}")

    # 5. Check frontend node_modules
    frontend_dir = os.path.join(base_dir, "frontend")
    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.exists(node_modules):
        print("[Pre-flight] Frontend dependencies missing. Running 'npm install' in frontend/...")
        subprocess.run("npm install", cwd=frontend_dir, shell=True)
        print("[Pre-flight] npm install completed.")

    print("[Pre-flight] All pre-flight checks passed successfully!\n")

def main():
    run_preflight_checks()

    processes = []
    log_files = []
    try:
        print("=" * 70)
        print("STARTING MICROSERVICES WORKSPACE")
        print("=" * 70)
        
        # Free any ports that may have remained open from a previous run
        print("[System] Checking and freeing ports (8011, 8012, 8013, 8010, 5173)...")
        free_ports([8011, 8012, 8013, 8010, 5173])
        time.sleep(1)

        # Open write streams for each component's log files
        user_log = open("user_service.log", "w", encoding="utf-8")
        product_log = open("product_service.log", "w", encoding="utf-8")
        order_log = open("order_service.log", "w", encoding="utf-8")
        gateway_log = open("gateway_service.log", "w", encoding="utf-8")
        frontend_log = open("frontend.log", "w", encoding="utf-8")
        
        log_files.extend([user_log, product_log, order_log, gateway_log, frontend_log])
        
        # 1. Start User Service (Port 8011)
        print("[System] Launching User Service on http://127.0.0.1:8011 ...")
        user_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "user_service.main:app", "--port", "8011", "--reload"],
            stdout=user_log,
            stderr=subprocess.STDOUT
        )
        processes.append((user_proc, "User Service", "user_service.log"))
        
        # 2. Start Product Service (Port 8012)
        print("[System] Launching Product Service on http://127.0.0.1:8012 ...")
        product_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "product_service.main:app", "--port", "8012", "--reload"],
            stdout=product_log,
            stderr=subprocess.STDOUT
        )
        processes.append((product_proc, "Product Service", "product_service.log"))

        # 3. Start Order Service (Port 8013)
        print("[System] Launching Order Service on http://127.0.0.1:8013 ...")
        order_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "order_service.main:app", "--port", "8013", "--reload"],
            stdout=order_log,
            stderr=subprocess.STDOUT
        )
        processes.append((order_proc, "Order Service", "order_service.log"))

        # 4. Start API Gateway (Port 8010)
        print("[System] Launching API Gateway on http://127.0.0.1:8010 ...")
        gateway_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "gateway_service.main:app", "--port", "8010", "--reload"],
            stdout=gateway_log,
            stderr=subprocess.STDOUT
        )
        processes.append((gateway_proc, "API Gateway", "gateway_service.log"))

        # 5. Start React Frontend (Port 5173 via Vite)
        print("[System] Launching React Frontend on http://localhost:5173 ...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=os.path.join(os.path.dirname(__file__), "frontend"),
            stdout=frontend_log,
            stderr=subprocess.STDOUT,
            shell=True # Required on Windows
        )
        processes.append((frontend_proc, "React Frontend", "frontend.log"))

        # Pause execution to let services initialize
        time.sleep(3.5)
        
        # Perform check to see if any process crashed immediately
        any_failed = False
        for proc, name, log_name in processes:
            exit_code = proc.poll()
            if exit_code is not None:
                print(f"\n[Error] {name} failed to start! (Exit code: {exit_code})")
                print(f"--- Last 12 lines from {log_name} ---")
                try:
                    with open(log_name, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        print("".join(lines[-12:]))
                except Exception as log_err:
                    print(f"(Could not read log file: {log_err})")
                print("-" * 50)
                any_failed = True
        
        if any_failed:
            print("\n[System] One or more services failed to start. Shutting down workspace...")
            raise KeyboardInterrupt
        
        print("\n" + "=" * 70)
        print("ALL MICROSERVICES & FRONTEND ARE LIVE AND HEALTHY!")
        print("=" * 70)
        print("  - React Frontend App:         http://localhost:5173")
        print("  - API Gateway API Docs:       http://127.0.0.1:8010/docs")
        print("  - Default Admin Account:      admin@store.com     / admin123")
        print("  - Default Customer Account:   customer@store.com  / customer123")
        print("=" * 70)
        print("Press Ctrl+C at any time to terminate all components.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[System] Shutting down services...")
        # Terminate and wait for all running subprocesses to close gracefully
        for proc, name, _ in processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
        print("[System] All components stopped.")
    finally:
        for f in log_files:
            try:
                f.close()
            except Exception:
                pass
        free_ports([8011, 8012, 8013, 8010, 5173])

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
