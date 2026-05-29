import sys
import subprocess

def main():
    print("Running Alembic migrations...")
    # Usiamo sys.executable per chiamare alembic tramite Python
    # Questo evita problemi con l'estensione (.exe o assente) sui diversi sistemi operativi
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])
    
    if result.returncode != 0:
        print("Alembic migrations failed.")
        sys.exit(result.returncode)

    print("Starting server...")
    # Usiamo sys.executable per chiamare uvicorn, compatibile sia su Windows che su Linux
    result = subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
