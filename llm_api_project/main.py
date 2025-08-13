from dotenv import load_dotenv
from silicon_provider import SiliconProvider
from google_provider import GoogleProvider
from typing import Dict, Optional

# 加载环境变量
load_dotenv()

class LLMManager:
    def __init__(self):
        self.providers: Dict[str, type] = {
            'silicon': SiliconProvider,
            'google': GoogleProvider
        }
        self.current_provider = None
        self.current_model = None
        
    def initialize_provider(self, provider_name: str) -> bool:
        """初始化指定的提供商"""
        try:
            provider_class = self.providers.get(provider_name)
            if not provider_class:
                print(f"错误：未知的提供商 {provider_name}")
                return False
            
            self.current_provider = provider_class()
            self.current_model = self.current_provider.default_model
            return True
        except Exception as e:
            print(f"初始化提供商失败: {str(e)}")
            return False
    
    def switch_provider(self, provider_name: str) -> bool:
        """切换到指定的提供商"""
        return self.initialize_provider(provider_name)
    
    def get_available_models(self) -> Dict[str, str]:
        """获取当前提供商的可用模型"""
        if not self.current_provider:
            return {}
        return self.current_provider.get_available_models()
    
    def chat(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> str:
        """发送聊天请求"""
        if not self.current_provider:
            raise ValueError("未初始化任何提供商")
        
        return self.current_provider.chat_completion(
            messages=messages,
            model=model or self.current_model,
            temperature=temperature
        )

def main():
    manager = LLMManager()
    
    # 默认使用硅基流动
    if not manager.initialize_provider('silicon'):
        # 如果硅基流动初始化失败，尝试使用Google
        if not manager.initialize_provider('google'):
            print("错误：无法初始化任何API提供商")
            return
    
    print("欢迎使用AI对话系统！")
    print("可用命令：")
    print("- 输入'切换'可以在硅基流动和Google之间切换")
    print("- 输入'模型'可以切换模型")
    print("- 输入'退出'结束对话")
    print("- 输入'帮助'查看命令列表")
    print(f"\n当前API提供商: {manager.current_provider.__class__.__name__}")
    print(f"当前模型: {manager.current_model}")
    
    # 存储对话历史
    messages = []
    
    while True:
        # 获取用户输入
        user_input = input("\n您: ").strip()
        
        # 处理特殊命令
        if user_input.lower() in ['退出', 'quit', 'exit']:
            print("再见！")
            break
        elif user_input.lower() == '切换':
            current = 'silicon' if isinstance(manager.current_provider, GoogleProvider) else 'google'
            if manager.switch_provider(current):
                print(f"已切换到 {current}")
                print(f"当前模型: {manager.current_model}")
            continue
        elif user_input.lower() == '模型':
            models = manager.get_available_models()
            print("\n可用模型:")
            for key, model in models.items():
                print(f"{key}: {model}")
            choice = input("请选择模型编号: ")
            if choice in models:
                manager.current_model = models[choice]
                print(f"已切换到模型: {manager.current_model}")
            else:
                print("无效的选择")
            continue
        elif user_input.lower() == '帮助':
            print("\n可用命令：")
            print("- 输入'切换'可以在硅基流动和Google之间切换")
            print("- 输入'模型'可以切换模型")
            print("- 输入'退出'结束对话")
            print("- 输入'帮助'查看命令列表")
            continue
            
        # 添加用户消息到历史记录
        messages.append({"role": "user", "content": user_input})
        
        try:
            # 发送请求并获取响应
            response = manager.chat(messages)
            # 添加AI响应到历史记录
            messages.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main() 