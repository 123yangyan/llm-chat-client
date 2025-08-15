"""
MCP Client Example

这个模块提供了MCP客户端的使用示例。
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

from mcp_service.client.mcp_client import create_client

def parse_search_results(results: Any) -> List[Dict[str, Any]]:
    """
    解析搜索结果为列表

    Args:
        results: 搜索结果（可能是字符串、列表或其他格式）

    Returns:
        List[Dict[str, Any]]: 解析后的结果列表
    """
    try:
        # 如果是列表且只有一个元素，提取第一个元素
        if isinstance(results, list) and len(results) == 1:
            first_item = results[0]
            # 如果是TextContent格式的字符串
            if isinstance(first_item, str) and "type='text'" in first_item:
                # 提取text字段的内容
                text_start = first_item.find("text='") + len("text='")
                text_end = first_item.rfind("'")
                if text_start > 0 and text_end > text_start:
                    json_str = first_item[text_start:text_end].replace('\\n', '\n').replace('\\"', '"')
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"解析JSON时出错: {e}")
                        print(f"JSON字符串: {json_str}")
                        return []

        # 如果是字符串，尝试解析
        if isinstance(results, str):
            # 如果是TextContent格式
            if "type='text'" in results:
                # 提取text字段的内容
                text_start = results.find("text='") + len("text='")
                text_end = results.rfind("'")
                if text_start > 0 and text_end > text_start:
                    json_str = results[text_start:text_end].replace('\\n', '\n').replace('\\"', '"')
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"解析JSON时出错: {e}")
                        print(f"JSON字符串: {json_str}")
                        return []
            # 如果是普通JSON字符串
            return json.loads(results)

        # 如果已经是列表，直接返回
        if isinstance(results, list):
            return results

        print(f"未知的结果格式: {type(results)}")
        print(f"结果内容: {results}")
        return []

    except Exception as e:
        print(f"解析搜索结果时发生错误: {e}")
        print(f"原始结果类型: {type(results)}")
        print(f"原始结果内容: {results}")
        return []

async def test_bing_search(client, query: str, num_results: int = 5) -> Optional[List[Dict[str, Any]]]:
    """
    测试必应搜索功能

    Args:
        client: MCP客户端实例
        query (str): 搜索关键词
        num_results (int): 返回结果数量

    Returns:
        Optional[List[Dict[str, Any]]]: 搜索结果，如果失败则返回None
    """
    print("\n=== 测试必应搜索 ===")
    
    # 调用bing_search工具
    arguments = {
        "query": query,
        "num_results": num_results
    }
    
    print(f"搜索关键词: {arguments['query']}")
    print(f"请求结果数量: {arguments['num_results']}")
    
    try:
        results = await client.call_tool(
            "bing_search", 
            arguments,
            timeout=30.0
        )
        
        if results:
            print("\n搜索结果:")
            print(f"原始结果类型: {type(results)}")
            
            # 解析结果
            parsed_results = parse_search_results(results)
            if parsed_results:
                # 显示结果
                for i, item in enumerate(parsed_results, 1):
                    print(f"\n[{i}] {'-'*50}")
                    if isinstance(item, dict):
                        print(f"标题: {item.get('title', '无标题')}")
                        print(f"链接: {item.get('link', '无链接')}")
                        print(f"摘要: {item.get('snippet', '无摘要')}")
                        print(f"ID: {item.get('id', '无ID')}")
                    else:
                        print(f"结果: {item}")
                return parsed_results
            else:
                print("无法解析搜索结果")
                return None
        else:
            print("搜索失败")
            return None
            
    except Exception as e:
        print(f"搜索过程中发生错误: {e}")
        print(f"错误详情:", e.__class__.__name__)
        import traceback
        traceback.print_exc()
        return None

async def test_fetch_webpage(client, result_id: str) -> bool:
    """
    测试网页内容获取功能

    Args:
        client: MCP客户端实例
        result_id (str): 搜索结果ID

    Returns:
        bool: 是否成功获取内容
    """
    print("\n=== 测试网页内容获取 ===")
    
    # 调用fetch_webpage工具
    arguments = {
        "result_id": result_id
    }
    
    print(f"获取网页ID: {result_id}")
    
    try:
        result = await client.call_tool(
            "fetch_webpage", 
            arguments,
            timeout=30.0
        )
        
        if result:
            print("\n网页内容:")
            if isinstance(result, dict):
                print(f"标题: {result.get('title', '无标题')}")
                content = result.get('content', '')
                print(f"内容长度: {len(content)} 字符")
                print("\n内容预览（前500字符）:")
                preview = content[:500] + ('...' if len(content) > 500 else '')
                print(preview)
            elif isinstance(result, str):
                print("内容预览（前500字符）:")
                preview = result[:500] + ('...' if len(result) > 500 else '')
                print(preview)
            else:
                print(f"未知的结果格式: {type(result)}")
                print("原始结果:", result)
            return True
        else:
            print("获取网页内容失败")
            print("注意：某些网站可能有反爬虫措施，导致无法获取内容")
            return False
            
    except Exception as e:
        print(f"获取网页内容时发生错误: {e}")
        return False

async def main():
    """主函数"""
    # 从环境变量获取MCP服务URL
    mcp_url = os.getenv('MCP_HOSTED_URL')
    if not mcp_url:
        print("请先设置MCP_HOSTED_URL环境变量")
        return
    
    try:
        # 创建MCP客户端
        async with create_client(mcp_url) as client:
            # 1. 先进行必应搜索
            search_results = await test_bing_search(client, "苏超", 5)
            
            # 2. 如果搜索成功，让用户选择要获取哪篇文章的内容
            if search_results and len(search_results) > 0:
                try:
                    print("\n请选择要获取内容的文章编号(1-5)，或按Ctrl+C退出：")
                    choice = int(input("请输入数字: ").strip())
                    if 1 <= choice <= len(search_results):
                        selected_result = search_results[choice - 1]
                        result_id = selected_result.get('id')
                        if result_id:
                            await test_fetch_webpage(client, result_id)
                        else:
                            print("\n所选文章没有有效的ID")
                    else:
                        print("\n无效的选择，请输入1到5之间的数字")
                except (ValueError, IndexError):
                    print("\n输入无效，请输入1到5之间的数字")
                except KeyboardInterrupt:
                    print("\n操作已取消")
            else:
                print("\n无法进行网页内容获取测试，因为搜索未返回结果")
                
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
    finally:
        print("\n程序执行完成")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序异常退出: {e}") 