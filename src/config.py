"""アプリケーション設定。環境変数から読み込む。"""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    raindrop_token: str = ""
    raindrop_collection_id: int = 0
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = ""
    max_summarize_per_run: int = 10
    request_timeout_seconds: int = 20
    user_agent: str = "RaindropSummarizer/0.1"
    output_dir: str = "docs"
    data_dir: str = "data"
    state_dir: str = "state"
    log_level: str = "INFO"

    def validate_required(self) -> list[str]:
        """必須設定の未設定項目を返す。"""
        errors: list[str] = []
        if not self.raindrop_token:
            errors.append("RAINDROP_TOKEN")
        if not self.raindrop_collection_id:
            errors.append("RAINDROP_COLLECTION_ID")
        if not self.llm_api_key:
            errors.append("LLM_API_KEY")
        if not self.llm_model:
            errors.append("LLM_MODEL")
        return errors
