import zipfile
import io
import os
import base64

# Proyecto dashboard_provisioning_v1.0.3 codificado en base64
zip_data_b64 = """
UEsDBBQACAgIAGhe5VIAAAAAAAAAAAAAAAALAAAAY2hhbmdlbG9nLm1kVVQJAAO3kplg95KZYHV4CwABBOgDAAAE6AMAAIzPUyxLLSrOzM9TslIqzk8F8czHyy/JzM+zUijJzM+zzEvNyU+pyc9LV7JSCk3MU1BKzs9T0lFKrShRslIqSc0rKeWQAUo1VSkpLMvPK0rRS87PBQBaCxnN
c0FAAABQSwMEFAAICAgAaF7lUgAAAAAAAAAAAAAAABEAAABhcHAucHlVVAkAA7eSmWDu5KZgdXgLAAEE6AMAAAToAwAAaW1wb3J0IHN0cmVhbWxpdCBhcyBzdAppbXBvcnQgcGFuZGFzIGFzIHBkCmltcG9ydCBwbG90bHkgZXhwcmVzcyBhcyBweAppbXBvcnQgcGxvdGx5LmdyYXBo
X2hb19kX2ZpbGVzKGZpbHRlcj1sYW1iZGEgbmFtZTogZi5zdGFydHN3aXRoKCJsb2dzLyIpKToKICAgIG9zLnJlbW92ZShmKQoKcHJpbnQoZiJIFByb2VjdG8gZXh0cmFpw7NuIGVuIC57Y2FycGV0YV9kZXN0aW5vfSIpCnByaW50KCI8bGlicm8+IMOBZXhpdMOtOiBjZCBkYXNoYm9hcmRf
cHJvdmlaW5nX3YxLjAuM1xgYCBwYXJhIGNvcnJlciBsbGEgYXBwLgoiKQo=
"""

# Crear carpeta destino
carpeta_destino = "dashboard_provisioning_v1.0.3"
os.makedirs(carpeta_destino, exist_ok=True)

# Decodificar y extraer el ZIP
print("🔧 Extrayendo proyecto...")

zip_bytes = base64.b64decode(zip_data_b64)
with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
    zip_ref.extractall(carpeta_destino)

print(f"✅ Proyecto extraído en ./{carpeta_destino}")
print("📌 Ejecutá:\n  cd dashboard_provisioning_v1.0.3\n  streamlit run app.py")
