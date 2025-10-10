{ pkgs, lib, config, inputs, ... }:

{
  packages = [ 
    pkgs.git
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
  '';
}
