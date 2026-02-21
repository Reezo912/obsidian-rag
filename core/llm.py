from config import LLM_MODEL, LLM_BASE_URL
from openai import OpenAI


class LLM:
    def __init__(self):
        self.model = LLM_MODEL
        self.base_url = LLM_BASE_URL
        self.client = self._connect()
        self.prompt = ""

    
    def _connect(self):
        """Connects to the LLM using LM Studio"""
        return OpenAI(api_key="None", base_url=self.base_url)

    def _build_prompt(self, query, context):
        self.prompt = f"""
        Use the following context to respond the question, in case of not founding any useful information, respond saying "there is no information available"
        CONTEXT:
        {context}

        QUESTION:   {query}

        ANSWER:
        """
        return self.prompt

    def get_answer(self, query, context):
        self._build_prompt(query, context)
        if not self.prompt:
            raise ValueError("THERE IS NO PROMPT TO PROCESS")
        response = self.client.responses.create(input=self.prompt, model=self.model)
        return response.output_text