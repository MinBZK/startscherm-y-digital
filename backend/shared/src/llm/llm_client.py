import os
from transformers import AutoTokenizer
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings, ChatOpenAI


class LLMClient:
    VECTOR_DIMS = 1024

    def __init__(self):
        self.default_llm = os.getenv("DEFAULT_LLM", "vlam")
        if self.default_llm == "vlam":
            self.default_embeddings = "gpt"
        else:
            self.default_embeddings = os.getenv("DEFAULT_LLM", "gpt")

        self.llm = self._initialize_llm()
        self.embeddings = self._initialize_embeddings()

    def _initialize_llm(self):
        if self.default_llm == "gpt":
            gpt_deployment_name = os.getenv("GPT_DEPLOYMENT_NAME")
            gpt_api_key = os.getenv("GPT_API_KEY")
            gpt_api_version = os.getenv("GPT_API_VERSION")
            gpt_endpoint = os.getenv("GPT_ENDPOINT")
            
            if not gpt_deployment_name:
                raise ValueError("GPT_DEPLOYMENT_NAME environment variable is not set")
            if not gpt_api_key:
                raise ValueError("GPT_API_KEY environment variable is not set")
            if not gpt_api_version:
                raise ValueError("GPT_API_VERSION environment variable is not set")
            if not gpt_endpoint:
                raise ValueError("GPT_ENDPOINT environment variable is not set")
            
            return AzureChatOpenAI(
                deployment_name=gpt_deployment_name,
                temperature=0,
                api_key=gpt_api_key,
                api_version=gpt_api_version,
                azure_endpoint=gpt_endpoint,
            )
        elif self.default_llm == "mistral":
            mistral_deployment_name = os.getenv("MISTRAL_DEPLOYMENT_NAME", "mistral-medium-latest")
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            
            if not mistral_api_key:
                raise ValueError("MISTRAL_API_KEY environment variable is not set")
            
            return ChatMistralAI(
                model=mistral_deployment_name,
                temperature=0,
                api_key=mistral_api_key,
            )
        elif self.default_llm == "vlam":
            vlam_model_name = os.getenv(
                "VLAM_MODEL_NAME",
                "ubiops-deployment/bzk-bsw-chat//chat-model"
            )
            vlam_api_key = os.getenv("VLAM_API_KEY")
            vlam_base_url = os.getenv(
                "VLAM_BASE_URL",
                "https://api.demo.vlam.ai/v2.1/projects/poc/openai-compatible/v1"
            )
            
            if not vlam_api_key:
                raise ValueError("VLAM_API_KEY environment variable is not set")
            
            return ChatOpenAI(
                model_name=vlam_model_name,
                openai_api_key=vlam_api_key,
                base_url=vlam_base_url,
                temperature=0,
                stream_usage=True
            )
        else:
            raise ValueError(f"Unsupported LLM: {self.default_llm}")
        
    def get_model(self):
        """Get the LLM model instance."""
        return self.llm

    def _initialize_embeddings(self):
        if self.default_embeddings == "gpt":
            embeddings_model_name = os.getenv("EMBEDDINGS_MODEL_NAME")
            embeddings_api_key = os.getenv("EMBEDDINGS_API_KEY")
            embeddings_api_version = os.getenv("EMBEDDINGS_API_VERSION")
            embeddings_endpoint = os.getenv("EMBEDDINGS_ENDPOINT")
            
            if not embeddings_model_name:
                raise ValueError("EMBEDDINGS_MODEL_NAME environment variable is not set")
            if not embeddings_api_key:
                raise ValueError("EMBEDDINGS_API_KEY environment variable is not set")
            if not embeddings_api_version:
                raise ValueError("EMBEDDINGS_API_VERSION environment variable is not set")
            if not embeddings_endpoint:
                raise ValueError("EMBEDDINGS_ENDPOINT environment variable is not set")
            
            return AzureOpenAIEmbeddings(
                model=embeddings_model_name,
                api_key=embeddings_api_key,
                api_version=embeddings_api_version,
                azure_endpoint=embeddings_endpoint,
                dimensions=self.VECTOR_DIMS,
            )
        elif self.default_embeddings == "mistral":
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                raise ValueError("MISTRAL_API_KEY environment variable is not set")

            embeddings_model = MistralAIEmbeddings(
                model=os.getenv("MISTRAL_EMBEDDINGS_MODEL", "mistral-embed"),
                api_key=mistral_api_key,
            )
            return embeddings_model
        else:
            raise ValueError(f"Unsupported embeddings model: {self.default_llm}")

    async def invoke(self, messages) -> str:
        ai_msg = await self.llm.ainvoke(messages)
        return ai_msg.content

    async def structured_invoke(self, schema, messages) -> str:
        try:
            self.structured_llm = self.llm.with_structured_output(schema)
            ai_msg = await self.structured_llm.ainvoke(messages)
            return ai_msg
        except Exception as e:
            raise ValueError(f"Error invoking structured LLM: {e}")

    async def get_embedding(self, query) -> list[float]:
        return await self.embeddings.aembed_query(query)

    async def bulk_embed(self, docs) -> list[list[float]]:
        return await self.embeddings.aembed_documents(docs)