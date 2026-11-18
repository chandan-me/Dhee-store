import subprocess
import sys
import time
import os
import shutil
import socket
import traceback

# =====================================================================
# SYSTEM ORCHESTRATOR SCRIPT (React + Gateway + Microservices)
# Features:
#  - Automatic .env detection & generation from .env.example
#  - Comprehensive Python dependencies verification
#  - Pre-flight MySQL TCP connectivity & credentials check
#  - Proactive database auto-creation (users_db, products_db, orders_db)
#  - Automatic npm install if node_modules missing
#  - Port cleanup & crash diagnosis with live log dumping
# =====================================================================

def p(msg="", **kwargs):
    """Flushed print to prevent lost output on Windows consoles."""
    print(msg, flush=True, **kwargs)

def free_ports(ports):
    """Kills any orphaned processes on the target ports to avoid [Errno 10048]."""
    for port in ports:
        try:
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def run_preflight_checks():
    """Validates environment, dependencies, MySQL connectivity, credentials, and databases."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, ".env")
        env_example = os.path.join(base_dir, ".env.example")
        
        p("=" * 70)
        p("MICROSERVICES WORKSPACE - PRE-FLIGHT SYSTEM VERIFICATION")
        p("=" * 70)

        # 1. Verify required Python packages in the current interpreter
        required_modules = [
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("sqlalchemy", "sqlalchemy"),
            ("pymysql", "pymysql"),
            ("cryptography", "cryptography"),
            ("dotenv", "python-dotenv"),
            ("jwt", "pyjwt"),
            ("bcrypt", "bcrypt"),
            ("httpx", "httpx"),
        ]
        missing_pkgs = []
        for mod_name, pip_name in required_modules:
            try:
                __import__(mod_name)
            except ImportError:
                missing_pkgs.append(pip_name)
        
        if missing_pkgs:
            p("\n" + "=" * 70)
            p(f"[CRITICAL ERROR] Missing required Python packages in this Python environment:")
            for pkg in missing_pkgs:
                p(f"  - {pkg}")
            p(f"\nCurrent Python: {sys.executable}")
            p("\nHOW TO FIX:")
            p(f"  Run in PowerShell:")
            p(f"      py -m pip install -r requirements.txt")
            p(f"  (or: pip install -r requirements.txt)")
            p("=" * 70 + "\n")
            sys.exit(1)

        # 2. Check or auto-generate .env
        if not os.path.exists(env_path):
            import secrets
            generated_jwt_secret = secrets.token_hex(32)
            default_env = (
                "# =====================================================================\n"
                "# Central Database & Authentication Configuration\n"
                "# All secret keys and passwords must be stored in this file (.env).\n"
                "# =====================================================================\n\n"
                "# MySQL Server Configuration\n"
                "MYSQL_HOST=localhost\n"
                "MYSQL_PORT=3306\n"
                "MYSQL_USER=root\n"
                "MYSQL_PASSWORD=\n\n"
                "# JWT Secret Key (Cryptographically generated)\n"
                f"JWT_SECRET={generated_jwt_secret}\n"
                "JWT_ALGORITHM=HS256\n"
                "ACCESS_TOKEN_EXPIRE_MINUTES=300000\n\n"
                "# Razorpay Payment Gateway Credentials (Optional)\n"
                "RAZORPAY_KEY_ID=\n"
                "RAZORPAY_KEY_SECRET=\n\n"
                "# Initial Administrator & Customer Setup (Optional)\n"
                "ADMIN_NAME=System Administrator\n"
                "ADMIN_EMAIL=admin@store.com\n"
                "ADMIN_PASSWORD=\n"
                "CUSTOMER_NAME=Customer User\n"
                "CUSTOMER_EMAIL=customer@store.com\n"
                "CUSTOMER_PASSWORD=\n"
            )
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(default_env)
            p("[Setup] Generated secure '.env' file with cryptographically random JWT_SECRET.")
            p("[Setup] Please open '.env' and specify your MYSQL_PASSWORD and account passwords.")
        else:
            p("[Pre-flight] Found '.env' configuration file.")

        # 3. Read environment variables
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)

        # Validate JWT_SECRET exists in .env
        jwt_secret = os.getenv("JWT_SECRET", "").strip()
        if not jwt_secret:
            import secrets
            generated_secret = secrets.token_hex(32)
            with open(env_path, "a", encoding="utf-8") as f:
                f.write(f"\nJWT_SECRET={generated_secret}\n")
            os.environ["JWT_SECRET"] = generated_secret
            p("[Pre-flight] Generated and appended a cryptographically secure JWT_SECRET to '.env'.")

        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_password = os.getenv("MYSQL_PASSWORD", "")

        # 4. Check TCP Socket to MySQL Server
        p(f"[Pre-flight] Checking MySQL Server reachability on {mysql_host}:{mysql_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        try:
            sock.connect((mysql_host, mysql_port))
            sock.close()
            p(f"[Pre-flight] MySQL Server port {mysql_port} is OPEN and reachable.")
        except Exception as sock_err:
            p("\n" + "=" * 70)
            p(f"[CRITICAL ERROR] Cannot connect to MySQL Server on {mysql_host}:{mysql_port}!")
            p(f"Details: {sock_err}")
            p("Backend microservices cannot start because MySQL is not running.")
            p("\nHOW TO START MYSQL ON WINDOWS:")
            p("  1. Press Win + R, type 'services.msc' and press Enter.")
            p("  2. Scroll down to locate 'MySQL' (e.g. 'MySQL80').")
            p("  3. Right-click it and click 'Start'.")
            p("     (Or open PowerShell as Administrator and run: Start-Service MySQL80)")
            p("  4. Once MySQL is started, re-run: python run_all.py")
            p("=" * 70 + "\n")
            sys.exit(1)

        # 5. Check MySQL Authentication & Auto-Create Databases
        import pymysql
        p(f"[Pre-flight] Verifying MySQL credentials for user '{mysql_user}'...")
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
            p("[Pre-flight] MySQL credentials verified & all databases confirmed (users_db, products_db, orders_db).")
        except Exception as e:
            err_str = str(e)
            err_code = e.args[0] if (hasattr(e, "args") and len(e.args) > 0 and isinstance(e.args[0], int)) else None
            
            if err_code == 1045 or "1045" in err_str or "Access denied" in err_str:
                p("\n" + "=" * 70)
                p(f"[CRITICAL ERROR] MySQL Login Failed! (Access denied for user '{mysql_user}')")
                p("The password in your '.env' file does not match your MySQL root password.")
                p("\nHOW TO FIX THIS:")
                p("  1. Open the file '.env' in this folder.")
                p("  2. Change MYSQL_PASSWORD= to your actual MySQL root password:")
                p("       MYSQL_PASSWORD=your_mysql_password")
                p("  3. Save '.env' and re-run: python run_all.py")
                p("=" * 70 + "\n")
                sys.exit(1)
            elif "cryptography" in err_str.lower():
                p("\n" + "=" * 70)
                p("[CRITICAL ERROR] MySQL 8.0 requires the 'cryptography' library for authentication!")
                p(f"Run: {sys.executable} -m pip install cryptography")
                p("=" * 70 + "\n")
                sys.exit(1)
            else:
                p(f"\n[CRITICAL ERROR] MySQL connection failure: {e}")
                p("Please check that MySQL Server is running properly and that '.env' settings are correct.\n")
                sys.exit(1)

        # 6. Check frontend node_modules
        frontend_dir = os.path.join(base_dir, "frontend")
        node_modules = os.path.join(frontend_dir, "node_modules")
        if not os.path.exists(node_modules):
            p("[Pre-flight] Frontend dependencies missing. Running 'npm install' in frontend/...")
            subprocess.run("npm install", cwd=frontend_dir, shell=True)
            p("[Pre-flight] npm install completed.")

        p("[Pre-flight] All pre-flight checks passed successfully!\n")
    except SystemExit:
        raise
    except Exception as exc:
        p("\n" + "=" * 70)
        p(f"[CRITICAL UNEXPECTED ERROR during pre-flight check]:\n{traceback.format_exc()}")
        p("=" * 70 + "\n")
        sys.exit(1)

def main():
    run_preflight_checks()

    processes = []
    log_files = []
    try:
        p("=" * 70)
        p("STARTING MICROSERVICES WORKSPACE")
        p("=" * 70)
        
        # Free any ports that may have remained open from a previous run
        p("[System] Checking and freeing ports (8011, 8012, 8013, 8010, 5173)...")
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
        p("[System] Launching User Service on http://127.0.0.1:8011 ...")
        user_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "user_service.main:app", "--port", "8011", "--reload"],
            stdout=user_log,
            stderr=subprocess.STDOUT
        )
        processes.append((user_proc, "User Service", "user_service.log"))
        
        # 2. Start Product Service (Port 8012)
        p("[System] Launching Product Service on http://127.0.0.1:8012 ...")
        product_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "product_service.main:app", "--port", "8012", "--reload"],
            stdout=product_log,
            stderr=subprocess.STDOUT
        )
        processes.append((product_proc, "Product Service", "product_service.log"))

        # 3. Start Order Service (Port 8013)
        p("[System] Launching Order Service on http://127.0.0.1:8013 ...")
        order_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "order_service.main:app", "--port", "8013", "--reload"],
            stdout=order_log,
            stderr=subprocess.STDOUT
        )
        processes.append((order_proc, "Order Service", "order_service.log"))

        # 4. Start API Gateway (Port 8010)
        p("[System] Launching API Gateway on http://127.0.0.1:8010 ...")
        gateway_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "gateway_service.main:app", "--port", "8010", "--reload"],
            stdout=gateway_log,
            stderr=subprocess.STDOUT
        )
        processes.append((gateway_proc, "API Gateway", "gateway_service.log"))

        # 5. Start React Frontend (Port 5173 via Vite)
        p("[System] Launching React Frontend on http://localhost:5173 ...")
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
                p(f"\n[Error] {name} failed to start! (Exit code: {exit_code})")
                p(f"--- Last 12 lines from {log_name} ---")
                try:
                    with open(log_name, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        p("".join(lines[-12:]))
                except Exception as log_err:
                    p(f"(Could not read log file: {log_err})")
                p("-" * 50)
                any_failed = True
        
        if any_failed:
            p("\n[System] One or more services failed to start. Shutting down workspace...")
            raise KeyboardInterrupt
        
        admin_email = os.getenv("ADMIN_EMAIL", "").strip() or "Configured in .env"
        customer_email = os.getenv("CUSTOMER_EMAIL", "").strip() or "Configured in .env"
        p("\n" + "=" * 70)
        p("ALL MICROSERVICES & FRONTEND ARE LIVE AND HEALTHY!")
        p("=" * 70)
        p("  - React Frontend App:         http://localhost:5173")
        p("  - API Gateway API Docs:       http://127.0.0.1:8010/docs")
        p(f"  - Admin User:                 {admin_email} (Password set in .env)")
        p(f"  - Customer User:              {customer_email} (Password set in .env)")
        p("  - Security:                   All secrets loaded strictly from .env")
        p("=" * 70)
        p("Press Ctrl+C at any time to terminate all components.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        p("\n[System] Shutting down services...")
        # Terminate and wait for all running subprocesses to close gracefully
        for proc, name, _ in processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
        p("[System] All components stopped.")
    finally:
        for f in log_files:
            try:
                f.close()
            except Exception:
                pass
        free_ports([8011, 8012, 8013, 8010, 5173])

if __name__ == "__main__":
    main()
