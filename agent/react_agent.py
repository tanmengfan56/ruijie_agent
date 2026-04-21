from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch


class ReactAgent:
    def __init__(self, tools=None):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=tools,
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, input_dict):
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

