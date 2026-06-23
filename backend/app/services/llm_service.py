"""LLM 服务：封装 MiMo API 调用，支持流式输出"""
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Optional

import httpx
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务：支持重试和流式输出"""

    def __init__(self):
        self._client: openai.AsyncOpenAI | None = None

    async def initialize(self):
        """初始化客户端"""
        self._client = openai.AsyncOpenAI(
            api_key=settings.MIMO_API_KEY or "placeholder",
            base_url=settings.MIMO_BASE_URL,
            http_client=httpx.AsyncClient(verify=False),
        )
        logger.info("LLM 服务已初始化, model=%s", settings.MIMO_LLM_MODEL)

    def _get_client(self) -> openai.AsyncOpenAI:
        if self._client is None:
            raise RuntimeError("LLM 服务未初始化")
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def call(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """调用 LLM（非流式）"""
        client = self._get_client()
        target_model = model or settings.MIMO_LLM_MODEL
        logger.info("[LLM] 非流式调用, model=%s, msg_count=%d", target_model, len(messages))

        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
            timeout=settings.LLM_TOTAL_TIMEOUT,
        )
        content = response.choices[0].message.content or ""
        logger.info("[LLM] 非流式响应完成, length=%d", len(content))
        return content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def call_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 16384,
    ) -> AsyncIterator[str]:
        """调用 LLM（流式输出）"""
        client = self._get_client()
        target_model = model or settings.MIMO_LLM_MODEL
        logger.info("[LLM] 流式调用, model=%s, msg_count=%d", target_model, len(messages))

        stream = await asyncio.wait_for(
            client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            ),
            timeout=settings.LLM_TOTAL_TIMEOUT,
        )

        chunk_count = 0
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_count += 1
                yield chunk.choices[0].delta.content

        logger.info("[LLM] 流式响应完成, chunks=%d", chunk_count)

    async def call_json(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> dict:
        """调用 LLM 并返回 JSON"""
        result = await self.call(messages, model, temperature, max_tokens)
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(result)


# 单例
llm_service = LLMService()
