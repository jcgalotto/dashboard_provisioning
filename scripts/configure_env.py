import os, re, getpass, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(ROOT, ".env")
EXAMPLE_PATH = os.path.join(ROOT, ".env.example")

def read_env(path):
    data = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k] = v
    return data

def write_env(path, data):
    order = [
        "ORACLE_DSN","ORACLE_USER","ORACLE_PASSWORD",
        "ORACLE_POOL_MIN","ORACLE_POOL_MAX",
        "JWT_SECRET","JWT_EXPIRES_MIN","LOG_FILE_PATH","VITE_API_BASE"
    ]
    with open(path, "w", encoding="utf-8") as f:
        for k in order:
            if k in data:
                f.write(f"{k}={data[k]}\n")

env = read_env(EXAMPLE_PATH)
env.update(read_env(ENV_PATH))

print("Configuración de credenciales Oracle para .env")

dsn_input = input("Pegá ORACLE_DSN (formato host:puerto/servicio) o dejá vacío para asistente: ").strip()
dsn_re = re.compile(r"^[^:\s]+:\d+/.+$")
if dsn_input and dsn_re.match(dsn_input):
    dsn = dsn_input
else:
    host = input(f"Host [{env.get('ORACLE_DSN','melideo19.claro.amx')}]: ").strip() or "melideo19.claro.amx"
    port = input("Puerto [1521]: ").strip() or "1521"
    service = input("Servicio [ARTPROD]: ").strip() or "ARTPROD"
    dsn = f"{host}:{port}/{service}"

user = input(f"Usuario Oracle [{env.get('ORACLE_USER','')}]: ").strip() or env.get("ORACLE_USER","")
pwd = getpass.getpass("Password Oracle: ").strip()

env["ORACLE_DSN"] = dsn
env["ORACLE_USER"] = user
env["ORACLE_PASSWORD"] = pwd
env.setdefault("ORACLE_POOL_MIN", "1")
env.setdefault("ORACLE_POOL_MAX", "5")
env.setdefault("JWT_SECRET", "change_me")
env.setdefault("JWT_EXPIRES_MIN", "60")
env.setdefault("LOG_FILE_PATH", "/var/log/app/app.log")
env.setdefault("VITE_API_BASE", "/api")

if os.path.exists(ENV_PATH):
    shutil.copyfile(ENV_PATH, ENV_PATH + ".bak")
write_env(ENV_PATH, env)

print(f"Listo. .env escrito en {ENV_PATH}")
if os.path.exists(ENV_PATH + ".bak"):
    print(f"Backup: {ENV_PATH}.bak")
