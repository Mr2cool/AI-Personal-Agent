# AI Personal Agent

Welcome to the AI Personal Agent project! This assistant leverages OpenAI's GPT models and Bright Data for real-time web search, with a modern Flask web UI, user authentication, admin controls, and multi-agent logic (manager, critic, fact-check, validation agents).

## Features
- **Modern Web UI**: Chat interface with avatars, streaming, and export.
- **OpenAI GPT Integration**: All chat and agent logic uses OpenAI's GPT models.
- **Bright Data Web Search**: Real-time web search (enable/disable as needed).
- **Multi-Agent System**: Manager, Critic, FactCheck, and Validator agents communicate via JSON for robust, validated answers.
- **User Auth & Admin**: Register/login, profile, admin user/chat management.
- **Memory**: Short-term (SQLite) and long-term (ChromaDB) memory for each user.
- **Extensible**: Add more tools, agents, or LLMs easily.

## Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/pramodkoujalagi/AI-Personal-Agent.git
   cd AI-Personal-Agent
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your `.env` file**
   ```env
   OPENAI_API_KEY=your_openai_api_key
   FLASK_SECRET_KEY=your_flask_secret
   BRIGHTDATA_API_KEY=your_brightdata_api_key  # (optional, for web search)
   BRIGHTDATA_DATASET_ID=your_brightdata_dataset_id  # (optional)
   ```

## Usage
- **Run the Flask app:**
  ```bash
  python3 app.py
  ```
- **Open in browser:**
  Visit [http://localhost:5000](http://localhost:5000)

- **Multi-Agent API:**
  POST to `/multi_agent_chat` with a `message` to see manager/critic/factcheck/validation flow in JSON.

## Customization
- To enable/disable Bright Data search, edit the `search_brightdata` function in `app.py`.
- To add more agents or tools, see `multi_agent_system.py` and `persona_agent.py`.

## Screenshots
See the `/ss/` folder for UI examples.

## License
MIT License

---

For more, see the code and comments in each file. Contributions welcome!


