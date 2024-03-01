import os
from dotenv import load_dotenv
import streamlit as st
from langchain import hub
from langchain.agents import AgentExecutor, Tool, AgentType, initialize_agent, load_tools
from langchain.chains import LLMMathChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.runnables import RunnableConfig
from langchain_openai import OpenAI
from langchain.agents import AgentType, initialize_agent, load_tools

load_dotenv()

st.set_page_config(
    page_title="Agent", page_icon="🌏", layout="wide", initial_sidebar_state="collapsed"
)

"# Hi, I am your Personal Agent. Ask me anything!😁"

# Setup credentials in Streamlit
user_openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", help="Set this to run your own custom questions."
)

if user_openai_api_key:
    openai_api_key = user_openai_api_key
    enable_custom = True
else:
    openai_api_key = "not_supplied"
    enable_custom = False

openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(temperature=0, streaming=True, openai_api_key=openai_api_key)
search = DuckDuckGoSearchAPIWrapper()
llm_math_chain = LLMMathChain.from_llm(llm)

tools = [
    Tool(
        name="Search",
        func=search.run,
        description="For current events",
    )
]

# react_agent = create_react_agent(llm, tools, hub.pull("hwchase17/react"))

react_agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)
mrkl = AgentExecutor(agent=react_agent, tools=tools)

if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        st.write("😊 Gathering Info...")
        st_callback = StreamlitCallbackHandler(st.container())
        response = react_agent.run(prompt, callbacks=[st_callback])
        st.write(response)
