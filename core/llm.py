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

    def _build_prompt(self, query, context, chat_history):
        """Builds the prompt for the LLM"""
        history_text = ""
        for past_query, past_answer in chat_history:
            history_text += f"USER: {past_query}\nASSISTANT: {past_answer}\n\n"
        self.prompt = f"""
        Use the following context to respond the question. 
        If you don't find the answer in the context or chat history, respond saying only: "there is no information available"

        CHAT HISTORY:
        {history_text}

        CONTEXT:
        {context}

        CURRENT QUESTION:   
        {query}

        ANSWER:
        """
        return self.prompt

    def get_answer(self, query, context, chat_history, requested_model=None, stream=False):
        """
        This method builds the prompt and then gets the answer from the LLM
        Args:
            query (str): The query to be answered
            context (str): The context to be used to answer the query
            chat_history (list): The chat history to be used to answer the query
            requested_model (str): Optional. The specific model requested by the UI.
            stream (bool): Whether to stream the response back
        
        Returns:
            str or generator: The answer to the query, or a generator if stream=True
        """
        self._build_prompt(query, context, chat_history)
        if not self.prompt:
            raise ValueError("THERE IS NO PROMPT TO PROCESS")
            
        # Get requested model by Open WebUI, or the default from config
        target_model = requested_model if requested_model else self.model
            
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": self.prompt}],
                stream=stream
            )
        except Exception as e:
            error_str = str(e).lower()
            if "failed to load model" in error_str:
                error_msg = f"Error loading model '{target_model}', check if there is a model loaded and the name in config.py is correct."
            else:
                error_msg = f"Error generating response: {str(e)}"
                
            print(error_msg)
            return (chunk for chunk in [error_msg]) if stream else error_msg
        
        if stream:
            return (chunk.choices[0].delta.content or "" for chunk in response)
        else:
            return response.choices[0].message.content