"""全局配置：通过环境变量 / .env 注入，pydantic-settings 管理。

设计取舍：把「模型」「安全」「服务」三类配置集中在一处，
便于评测时用同一套配置复现，也便于部署时注入不同环境。
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。所有字段均可被同名环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- LLM ----
    llm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen-plus"
    llm_temperature: float = 0.0
    # DeepSeek 等默认开启思考模式的模型，关掉以拿到确定性 JSON 输出并省 token
    llm_disable_thinking: bool = False

    # ---- 嵌入（RAG） ----
    embed_api_base: str = ""
    embed_api_key: str = ""
    embed_model: str = "text-embedding-v3"

    # ---- 安全管控 ----
    safety_dry_run: bool = True
    safety_mount_whitelist: str = "/mnt,/media,/dev/sd"
    safety_dangerous_commands: str = (
        "rm -rf,mkfs,dd if,fdisk --delete,shutdown,reboot"
    )

    # ---- 服务 ----
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    # ---- Agent 迭代上限 ----
    max_iterations: int = 6

    @property
    def mount_whitelist(self) -> list[str]:
        return [p for p in self.safety_mount_whitelist.split(",") if p]

    @property
    def dangerous_commands(self) -> list[str]:
        return [c for c in self.safety_dangerous_commands.split(",") if c]

    @property
    def use_real_llm(self) -> bool:
        """是否走真实模型（无 key 时自动退化为 FakeLLM）。"""
        return bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
