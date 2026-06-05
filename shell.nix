{ pkgs ? import <nixpkgs> {} }: pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    libGL
    glib
    ninja
    cmake
    gcc
    stdenv.cc.cc.lib
    nodejs_22
  ];
  shellHook = ''
    export NPM_CONFIG_PREFIX="$HOME/.npm-global"
    mkdir -p "$HOME/.npm-global/bin"

    if [ ! -d venv ]; then python3 -m venv venv; fi
    source venv/bin/activate

    # Re-set everything after venv activation
    export PATH="${pkgs.nodejs_22}/bin:$HOME/.npm-global/bin:$PWD/node_modules/.bin:$PATH"
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.libGL
      pkgs.glib
      pkgs.stdenv.cc.cc.lib
    ]}:$LD_LIBRARY_PATH"

    if ! command -v ng &> /dev/null; then
      echo "Instalando Angular CLI..."
      npm install -g @angular/cli
    fi
  '';
}