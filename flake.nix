# For local development on my machine
# You can ignore this file

{
  description = "Dev Shell for Python on NixOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          uv
          python313
          stdenv.cc.cc.lib
          zlib
        ];

        shellHook = ''
          export PYTHONPATH="$PYTHONPATH:$(pwd)"
          export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:$LD_LIBRARY_PATH"
          source .venv/bin/activate

          required_models=("qwen2.5:3b" "nomic-embed-text")

          for MODEL in $required_models; do
            if ! ollama list | grep -q "$MODEL"; then
              echo "Pulling $MODEL..."
              ollama pull "$MODEL"
            fi
          done
        '';

      };
    };
}
