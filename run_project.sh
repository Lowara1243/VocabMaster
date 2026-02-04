#!/bin/bash
# Script for project setup and startup

# Stop execution on any error
set -e

# --- Variables ---
FRONTEND_DIR="frontend"
# Flag file indicating initial setup is complete
SETUP_FLAG=".setup_complete"

# --- Logic ---

# Check if setup flag exists. If not, this is the first run.
if [ ! -f "$SETUP_FLAG" ]; then
  echo "--- First run detected. Performing initial setup... ---"

  # 1. Backend setup using uv sync
  echo "[1/4] Setting up Python virtual environment and dependencies..."
  # uv sync will create .venv in the root and install dependencies from pyproject.toml
  uv sync

  # 2. Frontend setup
  echo "[2/4] Installing Node.js dependencies and building frontend..."
  cd "$FRONTEND_DIR"
  npm install
  npm run build
  cd ..

  # 3. Create setup completion flag
  echo "[3/4] Setup complete."
  touch "$SETUP_FLAG"
  echo "--- Initial setup successfully completed. ---"
else
  echo "--- Skipping setup as project is already configured. ---"
fi

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    echo "Error: 'screen' not found. It is required for the background servers."
    echo "Please install it using your package manager:"
    echo "  - Debian/Ubuntu: sudo apt install screen"
    echo "  - Fedora: sudo dnf install screen"
    echo "  - Arch Linux: sudo pacman -S screen"
    exit 1
fi

echo "--- Starting servers... ---"

# Terminate old screen sessions if they exist to avoid conflicts
screen -X -S backend_session quit || true
screen -X -S frontend_session quit || true

# Run backend from project root
echo "Starting backend server in background session 'backend_session'..."
# uv run automatically uses the local .venv
screen -S backend_session -d -m bash -c "uv run python backend/run.py"

# Run frontend (Vite preview) in a new screen session
echo "Starting frontend server in background session 'frontend_session'..."
screen -S frontend_session -d -m bash -c "cd '$FRONTEND_DIR' && npm run preview -- --port 4173"

# Give servers a moment to start
sleep 2

echo ""
echo "------------------------------------------------------------------"
echo "✅ Done! Your application should be available at:"
echo "   http://localhost:4173"
echo "------------------------------------------------------------------"
echo ""
echo "Background process management:"
echo " - View backend logs: screen -r backend_session"
echo " - View frontend logs: screen -r frontend_session"
echo "   (To exit log view, press Ctrl+A, then D)"
echo ""
echo " - Stop backend: screen -X -S backend_session quit"
echo " - Stop frontend: screen -X -S frontend_session quit"
echo "------------------------------------------------------------------"
