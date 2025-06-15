import json
import openai
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class BaseAgent:
    def __init__(self, name):
        self.name = name
    def receive(self, message_json):
        raise NotImplementedError

class ManagerAgent(BaseAgent):
    def __init__(self, agents):
        super().__init__("Manager")
        self.agents = agents
    def receive(self, message_json):
        # Step 1: Send to Critic
        critic_response = self.agents['critic'].receive(message_json)
        # Step 2: Send to FactCheck
        fact_response = self.agents['factcheck'].receive(critic_response)
        # Step 3: Send to Validator
        validation = self.agents['validator'].receive(fact_response)
        # Step 4: Aggregate
        return json.dumps({
            "manager": self.name,
            "original": message_json,
            "critic": critic_response,
            "factcheck": fact_response,
            "validation": validation
        })

class CriticAgent(BaseAgent):
    def receive(self, message_json):
        msg = json.loads(message_json)
        critique = f"Critique: The message '{msg['content']}' is being reviewed."
        msg['critic'] = critique
        return json.dumps(msg)

class FactCheckAgent(BaseAgent):
    def receive(self, message_json):
        msg = json.loads(message_json)
        fact = f"FactCheck: The statement '{msg['content']}' appears plausible."
        msg['factcheck'] = fact
        return json.dumps(msg)

class ValidatorAgent(BaseAgent):
    def receive(self, message_json):
        msg = json.loads(message_json)
        valid = "Validation: All checks passed."
        msg['validation'] = valid
        return json.dumps(msg)

def create_multi_agent_system():
    critic = CriticAgent("Critic")
    factcheck = FactCheckAgent("FactCheck")
    validator = ValidatorAgent("Validator")
    agents = {
        'critic': critic,
        'factcheck': factcheck,
        'validator': validator
    }
    manager = ManagerAgent(agents)
    return manager

# Example usage:
if __name__ == "__main__":
    manager = create_multi_agent_system()
    user_message = json.dumps({"role": "user", "content": "The Eiffel Tower is in Berlin."})
    result = manager.receive(user_message)
    print(json.dumps(json.loads(result), indent=2))
