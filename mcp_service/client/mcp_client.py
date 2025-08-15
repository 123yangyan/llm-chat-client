"""
MCP Client Implementation

这个模块提供了ModelScope MCP服务的客户端实现。
"""

import asyncio
from contextlib import AsyncExitStack
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import RequestParams
from typing import Dict, Any, Optional

from ..config.settings import MCPSettings
from ..utils.logger import setup_logger

# 设置日志记录器
logger = setup_logger(__name__)

class MCPClientError(Exception):
    """MCP客户端错误基类"""
    pass

class ConnectionError(MCPClientError):
    """连接错误"""
    pass

class TimeoutError(MCPClientError):
    """超时错误"""
    pass

class MCPClient:
    """ModelScope MCP客户端类"""
    
    def __init__(self, mcp_url: str):
        """
        初始化MCP客户端

        Args:
            mcp_url (str): ModelScope MCP服务的专属SSE URL
        """
        self.mcp_url = mcp_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def connect(self) -> None:
        """
        连接到MCP服务器

        Raises:
            ConnectionError: 连接失败时抛出
        """
        try:
            # 创建SSE客户端
            self._streams_context = sse_client(url=self.mcp_url)
            streams = await self._streams_context.__aenter__()
            
            # 创建会话
            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()
            
            # 初始化会话
            await self.session.initialize()
            
            # 验证连接
            response = await self.session.list_tools()
            tools = response.tools
            logger.info(f"成功连接到MCP服务，可用工具: {[tool.name for tool in tools]}")
            
        except Exception as e:
            logger.error(f"连接MCP服务失败: {e}")
            await self.close()
            raise ConnectionError(f"无法连接到MCP服务: {e}")

    async def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        timeout: float = 30.0,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ) -> Optional[Any]:
        """
        调用MCP服务中的指定工具

        Args:
            tool_name (str): 要调用的工具名称
            arguments (Dict[str, Any]): 工具的输入参数
            timeout (float): 请求超时时间（秒）
            retry_count (int): 重试次数
            retry_delay (float): 重试延迟（秒）

        Returns:
            Optional[Any]: 工具的执行结果，如果发生错误则返回None

        Raises:
            TimeoutError: 请求超时
            ConnectionError: 连接错误
            MCPClientError: 其他客户端错误
        """
        if not self.session:
            raise ConnectionError("未连接到MCP服务")

        logger.info(f"准备调用工具: {tool_name}")
        logger.debug(f"输入参数: {json.dumps(arguments, indent=2, ensure_ascii=False)}")

        attempt = 0
        last_error = None

        while attempt < retry_count:
            attempt += 1
            try:
                # 设置超时
                async with asyncio.timeout(timeout):
                    # 调用工具
                    result = await self.session.call_tool(tool_name, arguments)
                    
                    # 处理结果
                    if result.content:
                        # 如果是流式内容
                        if hasattr(result.content, '__aiter__'):
                            full_output = ""
                            async for chunk in result.content:
                                full_output += str(chunk)
                                logger.debug(f"收到数据块: {chunk}")
                            return full_output
                            
                        # 如果是列表内容
                        elif isinstance(result.content, (list, tuple)):
                            return [str(item) for item in result.content]
                            
                        # 其他内容
                        return str(result.content)
                        
                    return None

            except asyncio.TimeoutError:
                last_error = f"请求超时（{timeout}秒）"
                logger.error(last_error)
                if attempt == retry_count:
                    raise TimeoutError(last_error)
                
            except ConnectionError as e:
                last_error = f"连接错误: {e}"
                logger.error(last_error)
                if attempt == retry_count:
                    raise
                
            except Exception as e:
                last_error = f"调用工具时发生错误: {e}"
                logger.error(last_error)
                logger.exception("详细错误信息")
                if attempt == retry_count:
                    raise MCPClientError(last_error)
            
            # 重试前等待
            if attempt < retry_count:
                delay = retry_delay * attempt
                logger.info(f"第 {attempt} 次重试失败，{delay} 秒后重试...")
                await asyncio.sleep(delay)
            
        return None

    async def close(self):
        """关闭客户端连接"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)
        self.session = None

class AsyncMCPClient:
    """异步MCP客户端工厂类"""
    
    def __init__(self, mcp_url: str = None):
        """
        初始化异步MCP客户端

        Args:
            mcp_url (str, optional): MCP服务的URL。如果不提供，将使用配置文件中的URL。
        """
        self.mcp_url = mcp_url or MCPSettings.HOSTED_URL
        self._client = None

    async def __aenter__(self) -> MCPClient:
        """异步上下文管理器入口"""
        self._client = MCPClient(self.mcp_url)
        await self._client.connect()
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._client:
            await self._client.close()

def create_client(mcp_url: str = None) -> AsyncMCPClient:
    """
    创建MCP客户端的工厂函数

    Args:
        mcp_url (str, optional): MCP服务的URL。如果不提供，将使用配置文件中的URL。

    Returns:
        AsyncMCPClient: 异步MCP客户端实例
    """
    return AsyncMCPClient(mcp_url) 