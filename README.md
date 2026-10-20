# Email Agent

A LangGraph-based Gmail classification and response agent.

## Project Structure

```text
email-agent/
│
├── app/
│   ├── agents/         # Agent workflows and logic
│   ├── graphs/         # LangGraph workflow definitions
│   ├── gmail/          # Gmail API connection and helpers
│   ├── llms/           # LLM configuration (e.g. Gemini, OpenAI)
│   ├── prompts/        # System prompts and templates
│   ├── schemas/        # Pydantic schemas/models
│   ├── tools/          # Custom tools (Gmail, Web Search, etc.)
│   ├── utils/          # General utility functions
│   ├── config.py       # Configuration loader
│   └── main.py         # Entrypoint
│
├── tests/              # Unit and integration tests
│
├── credentials/
│   ├── credentials.json # Google Cloud credentials (user-provided)
│   └── token.json      # Generated OAuth2 tokens (generated automatically)
│
├── .env                # Local environment variables
├── .gitignore          # Git exclusion rules
├── requirements.txt    # Python requirements
└── pyproject.toml      # Project configuration
```

## Setup & Installation

### 1. Install Dependencies
It is recommended to use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env` and fill in the required API keys:
```bash
# Edit .env and set GEMINI_API_KEY

Fill 
GEMINI_API_KEY or OPENROUTER_API_KEY
GMAIL_USER_EMAIL

```

### 3. Configure Google Gmail Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Gmail API**.
3. Configure the OAuth Consent Screen (external, add test users).
4. Go to **Credentials**, click **Create Credentials** -> **OAuth client ID** (Application type: Desktop App).
5. Download the JSON file, rename it to `credentials.json`, and place it in the `credentials/` folder.

## Running the Agent
Once credentials are set up, run the entrypoint:
```bash
python -m app.main
```
On first run, a browser window will open to authenticate and authorize access to your Gmail account. This will save a `token.json` in the `credentials/` directory.
