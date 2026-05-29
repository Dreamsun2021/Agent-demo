# main.py
from agent import Agent

def main():
    print("💡 简易 AI Agent 已启动（输入 'exit' 退出）\n")
    agent = Agent()

    while True:
        try:
            user_input = input("👤 你: ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("exit", "quit"):
            break

        try:
            answer = agent.chat(user_input)
            print(f"🤖 Agent: {answer}\n")
        except Exception as e:
            print(f"❌ 出错了: {e}")
            # 移除刚才加入的 user 消息（如果存在），避免历史污染
            if agent.memory.history and agent.memory.history[-1]["role"] == "user":
                agent.memory.history.pop()

if __name__ == "__main__":
    main()