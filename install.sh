#!/bin/bash

# Get the absolute path of the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Starting installation process.."

# Check if Conda is installed
if ! command -v conda &> /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Conda not found. Installing Miniconda.."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
    source "$HOME/miniconda/bin/activate"
fi

# Update system dependencies
echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Updating APT and installing system packages.."
sudo apt update -y
sudo apt install -y build-essential uuid-dev libgpgme-dev squashfs-tools libseccomp-dev wget pkg-config git cryptsetup-bin

# Check and remove existing Conda environment if it exists
if conda env list | grep -q "PTPP"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Environment 'PTPP' exists. Removing.."
    conda deactivate
    conda env remove --name PTPP -y || { echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Failed to remove environment. Aborting!"; exit 1; }
fi

# Create environment from environment.yml
echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Creating Conda environment 'PTPP'.."
conda env create -f environment.yml -y || { echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Failed to create Conda environment. Aborting!"; exit 1; }

# Optionally, install R packages (if R is part of the env)
# Uncomment the line below if R is required and R packages are used
# conda run -n PTPP R -e "install.packages('ggplot2')"

# Compile C++ executable if needed (e.g., PTPP has a native component)
if [ -f "$SCRIPT_DIR/main.cpp" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Compiling C++ executable.."
    mkdir -p "$SCRIPT_DIR/bin"
    g++ -std=c++20 "$SCRIPT_DIR/main.cpp" -o "$SCRIPT_DIR/bin/ptpp_exe" `pkg-config --cflags --libs gtkmm-3.0` || {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] C++ compilation failed!"
        exit 1
    }

    # Create wrapper script
    cat << EOF > "$SCRIPT_DIR/ptpp_app"
#!/bin/bash

SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p "\$SCRIPT_DIR/inputs"
mkdir -p "\$SCRIPT_DIR/outputs"

eval "\$(conda shell.bash hook)"
conda activate PTPP
exec "\$SCRIPT_DIR/bin/ptpp_exe" "\$@"
EOF

    chmod +x "$SCRIPT_DIR/ptpp_app"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] C++ wrapper script 'ptpp_app' created successfully."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')][PTPP INSTALL] Installation complete! Run ./ptpp_app to start the program (if compiled)."
