{ pkgs, lib, config, inputs, ... }:

let
  # Install openspec from npm as a Nix package
  openspec = pkgs.buildNpmPackage rec {
    pname = "openspec";
    version = "latest";
    
    src = pkgs.fetchFromGitHub {
      owner = "fission-ai";
      repo = "openspec";
      rev = "main";
      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };
    
    npmDepsHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    
    dontNpmBuild = true;
  };
in
{
  packages = [ 
    pkgs.git
    # Use npx to run openspec from node_modules
    (pkgs.writeShellScriptBin "openspec" ''
      exec ${pkgs.nodejs_20}/bin/npx -y @fission-ai/openspec@latest "$@"
    '')
  ];

  languages.python = {
    enable = true;
    version = "3.11";
    venv.enable = true;
    venv.requirements = ./backend/requirements.txt;
  };

  languages.javascript = {
    enable = true;
    package = pkgs.nodejs_20;
    npm.enable = true;
    npm.install.enable = true;
  };

  processes.backend = {
    exec = "cd backend && python app.py";
  };

  processes.frontend = {
    exec = "cd frontend && npm run dev";
  };

  enterShell = ''
    echo "🛒 Superquinquin Members History - Development Environment"
    echo ""
    echo "Backend: Flask API on http://localhost:5000"
    echo "Frontend: React app on http://localhost:5173"
    echo ""
    echo "Configure backend/.env with your Odoo credentials before starting"
    echo ""
    echo "Run 'devenv up' to start both services"
    echo ""
    echo "✨ OpenSpec available via 'openspec' command"
  '';
}
