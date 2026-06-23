# almuthaqafun
Fanar Hackathon 2026 Project. An agentic AI framework for Qatari and Islamic heritage exploration.

## Local Setup
1. Set up the virtual environment
```
# Navigate to the repository directory
cd almuthaqafun

# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Ensure pip is updated to the latest version
pip install --upgrade pip
```

2. Install core dependencies
```
pip install fastapi uvicorn pydantic requests python-dotenv
```

3. Create .env file at root folder to define environment variables
```
FANAR_API_KEY=Your_API_Key
FANAR_BASE_URL=https://api.fanar.qa
FANAR_MODEL=Fanar-C-2-27B
```
3. Start local server
```
PYTHONPATH=. uvicorn src.main:app --reload --port 8000
```
4. Open client/client.html in a browser (e.g. Google Chrome)
