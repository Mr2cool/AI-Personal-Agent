import datetime
from typing import List, Dict, Any, Tuple, Callable
import openai
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class EpisodicMemory:
    """Stores fine-grained, time-stamped user interactions."""
    def __init__(self):
        self.events: List[Tuple[str, str, Dict[str, Any]]] = []

    def add_event(self, query: str, response: str, metadata: Dict[str, Any] = None):
        if metadata is None:
            metadata = {"timestamp": datetime.datetime.now().isoformat()}
        self.events.append((query, response, metadata))

    def retrieve(self, query: str = "", top_k: int = 4) -> List[Tuple[str, str, Dict[str, Any]]]:
        # Placeholder: In production, use semantic similarity search
        return self.events[-top_k:]

class SemanticMemory:
    """Stores abstracted user profile and preferences."""
    def __init__(self):
        self.profile: str = ""

    def update(self, episodic_events: List[Tuple[str, str, Dict[str, Any]]]):
        # Summarize last N events as profile
        self.profile = "; ".join([f"Q: {q} | A: {a}" for q, a, _ in episodic_events[-3:]])

    def get_profile(self) -> str:
        return self.profile

class PersonaAgent:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.persona_prompt = self._init_persona_prompt()

    def _init_persona_prompt(self) -> str:
        return (
            "You are a helpful personalized assistant. Take more than two actions to infer the user preference and answer the question. "
            "User summary: [Initial Semantic Memory]\n"
            "STRICT RULES: when using tools, always:\n"
            "1. Think step-by-step about what information you need.\n"
            "2. MUST use at least TWO tools to answer the question.\n"
            "3. Use tools precisely and deliberately and try to get the most accurate information from different tools.\n"
            "4. Provide clear, concise responses. Do not give explanation in the final answer."
        )

    def update_memories(self, query: str, response: str):
        self.episodic_memory.add_event(query, response)
        self.semantic_memory.update(self.episodic_memory.events)

    def get_persona(self) -> str:
        return self.persona_prompt.replace("[Initial Semantic Memory]", self.semantic_memory.get_profile())

    def act(self, query: str, tools: Dict[str, Callable[[str], str]]) -> str:
        # Use at least two tools if available
        tool_names = list(tools.keys())
        results = []
        for name in tool_names[:2]:
            result = tools[name](query)
            results.append(f"{name.capitalize()}: {result}")
        memory_result = self.episodic_memory.retrieve(query)
        memory_str = "; ".join([f"Q: {q} | A: {a}" for q, a, _ in memory_result]) if memory_result else "No memory found."
        response = "\n".join(results) + f"\nMemory: {memory_str}"
        self.update_memories(query, response)
        return response

    def llm_response(self, query: str, tools: Dict[str, Callable[[str], str]], model: str = "gpt-3.5-turbo") -> str:
        persona = self.get_persona()
        tool_context = "\n".join([f"{name}: {func(query)}" for name, func in tools.items()])
        messages = [
            {"role": "system", "content": persona},
            {"role": "user", "content": f"{query}\n{tool_context}"}
        ]
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1
        )
        answer = response.choices[0].message.content.strip()
        self.update_memories(query, answer)
        return answer

    def test_time_alignment(self, recent_interactions: List[Dict[str, str]]):
        feedback = []
        for interaction in recent_interactions:
            feedback.append(f"Align to preference: {interaction.get('feedback', '')}")
        self.persona_prompt += "\n" + "\n".join(feedback)

# Example tool functions
def wiki_tool(query: str) -> str:
    return f"Summary for '{query}' (from Wikipedia)"

def brightdata_wiki_tool(query: str) -> str:
    BRIGHTDATA_USERNAME = os.getenv('BRIGHTDATA_USERNAME')
    BRIGHTDATA_PASSWORD = os.getenv('BRIGHTDATA_PASSWORD')
    BRIGHTDATA_HOST = 'brd.superproxy.io'
    BRIGHTDATA_PORT = 22225
    proxies = {
        'http': f'http://{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}',
        'https': f'http://{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}',
    }
    url = f'https://en.wikipedia.org/wiki/{query.replace(" ", "_")}'
    try:
        resp = requests.get(url, proxies=proxies, timeout=10)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            p = soup.find('p')
            return p.text.strip() if p else 'No summary found.'
        else:
            return f'Failed to fetch Wikipedia page for {query}.'
    except Exception as e:
        return f'Error: {e}'

def memory_tool(agent: PersonaAgent, query: str) -> str:
    events = agent.episodic_memory.retrieve(query)
    return "; ".join([f"Q: {q} | A: {a}" for q, a, _ in events]) if events else "No memory found."

# Usage example
def demo():
    agent = PersonaAgent(user_id="userA")
    tools = {
        "wiki": wiki_tool,
        "memory": lambda q: memory_tool(agent, q)
    }
    print("Initial persona:", agent.get_persona())
    response = agent.act("Tell me about sci-fi movies", tools)
    print("Agent response:", response)
    print("Updated persona:", agent.get_persona())
    llm_response = agent.llm_response("What are some popular sci-fi movies?", tools)
    print("LLM response:", llm_response)

if __name__ == "__main__":
    demo()
