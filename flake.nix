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
        ];

        shellHook = ''
          export PYTHONPATH="$PYTHONPATH:$(pwd)"
          source .venv/bin/activate

          if ! ollama list | grep -q "gemma3:270m"; then
            echo "Pulling gemma3:270m..."
            ollama pull gemma3:270m
          fi
        '';

      };
    };
}
