# UV Aliases for Precinct App
# Add these to your ~/.bashrc or ~/.zshrc for convenience

# Project shortcuts
alias precinct-setup='cd /home/bren/Home/Projects/HTML_CSS/precinct && ./setup-uv.sh'
alias precinct-dev='cd /home/bren/Home/Projects/HTML_CSS/precinct && ./setup-dev.sh'
alias precinct-start='cd /home/bren/Home/Projects/HTML_CSS/precinct && ./run-app.sh'
alias precinct-test='cd /home/bren/Home/Projects/HTML_CSS/precinct && ./run-tests.sh'
alias precinct-cd='cd /home/bren/Home/Projects/HTML_CSS/precinct'

# UV shortcuts (when in project directory)
alias uvr='uv run'
alias uvs='uv sync'
alias uva='uv add'
alias uvd='uv remove'
alias uvl='uv pip list'

# Python shortcuts with UV
alias py='uv run python'
alias pytest-uv='uv run pytest'
alias black-uv='uv run black .'
alias isort-uv='uv run isort .'
alias flake8-uv='uv run flake8 .'

# Quick environment activation
alias venv-activate='source .venv/bin/activate'

echo "UV aliases loaded for Precinct app!"
echo "Available commands:"
echo "  precinct-start  - Start the app"
echo "  precinct-test   - Run tests"
echo "  precinct-cd     - Navigate to project"
echo "  uvr <command>   - Run with UV"
echo "  py <script>     - Run Python with UV"