# desktop_app.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from agent import Agent
from logger import logger

# ──────────────── 配色 ────────────────
BG_MAIN = "#1e1e2e"
BG_CHAT = "#2a2a3c"
BG_INPUT = "#40444b"
FG = "#dcddde"
FG_SECONDARY = "#72767d"
ACCENT_BLURPLE = "#7289da"
ACCENT_GREEN = "#43b581"
USER_BUBBLE = "#2e4a7a"
AGENT_BUBBLE = "#3a3a5c"
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)

class DesktopChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Agent")
        self.root.geometry("800x600")
        self.root.minsize(500, 400)
        self.root.configure(bg=BG_MAIN)

        self.agent = Agent()
        self.processing = False

        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # 主容器
        main_frame = tk.Frame(self.root, bg=BG_MAIN)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部标题栏
        header = tk.Frame(main_frame, bg=BG_MAIN, height=40)
        header.pack(fill=tk.X, padx=12, pady=(8, 0))
        tk.Label(header, text="🥑 助手", font=("Segoe UI", 12, "bold"),
                 fg=FG, bg=BG_MAIN).pack(side=tk.LEFT)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=(4, 0))

        # 聊天消息区域（Canvas + 可滚动 Frame）
        chat_bg = tk.Frame(main_frame, bg=BG_CHAT)
        chat_bg.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(chat_bg, bg=BG_CHAT, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(chat_bg, orient=tk.VERTICAL, command=self.canvas.yview)
        self.msg_frame = tk.Frame(self.canvas, bg=BG_CHAT)

        self.msg_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw", tags="msg_frame")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮绑定
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # 底部输入区域
        bottom_bar = tk.Frame(main_frame, bg="#292b2f")
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)

        input_frame = tk.Frame(bottom_bar, bg=BG_INPUT, bd=0)
        input_frame.pack(fill=tk.X, padx=12, pady=(8, 4))

        self.entry = tk.Text(
            input_frame,
            height=3,
            font=FONT,
            bg=BG_INPUT,
            fg=FG,
            insertbackground=FG,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=8,
            wrap=tk.WORD
        )
        self.entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 6))
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", self._on_shift_enter)

        # 发送按钮
        send_btn = tk.Button(
            input_frame,
            text="➤",
            font=("Segoe UI", 14, "bold"),
            fg=FG,
            bg=BG_INPUT,
            activebackground=BG_INPUT,
            activeforeground=ACCENT_BLURPLE,
            relief=tk.FLAT,
            bd=0,
            command=self.send_message,
            cursor="hand2"
        )
        send_btn.pack(side=tk.RIGHT)

        # 底部工具栏
        toolbar = tk.Frame(bottom_bar, bg="#292b2f")
        toolbar.pack(fill=tk.X, padx=12, pady=(0, 6))

        self.clear_btn = tk.Button(toolbar, text="清空对话", font=FONT_SMALL, fg=FG_SECONDARY, bg="#292b2f",
                                   activebackground="#292b2f", activeforeground="#f04747",
                                   relief=tk.FLAT, bd=0, command=self.clear_chat, cursor="hand2")
        self.clear_btn.pack(side=tk.LEFT, padx=4)

        self.export_btn = tk.Button(toolbar, text="导出记录", font=FONT_SMALL, fg=FG_SECONDARY, bg="#292b2f",
                                    activebackground="#292b2f", activeforeground=ACCENT_BLURPLE,
                                    relief=tk.FLAT, bd=0, command=self.export_chat, cursor="hand2")
        self.export_btn.pack(side=tk.LEFT, padx=4)

        self.status_label = tk.Label(toolbar, text="就绪", font=FONT_SMALL, fg=FG_SECONDARY, bg="#292b2f")
        self.status_label.pack(side=tk.RIGHT, padx=4)

        # 初始欢迎消息
        self._add_system_message("欢迎使用 🥑！直接输入消息开始对话。")

    # ──────────────── 输入事件 ────────────────
    def _on_enter(self, event):
        self.send_message()
        return "break"

    def _on_shift_enter(self, event):
        self.entry.insert(tk.INSERT, "\n")
        return "break"

    # ──────────────── 发送消息逻辑 ────────────────
    def send_message(self):
        if self.processing:
            messagebox.showwarning("提示", "正在生成回复，请稍候...")
            return

        user_text = self.entry.get("1.0", tk.END).strip()
        if not user_text:
            return

        # 显示用户消息（右对齐）
        self._add_user_message(user_text)
        self.entry.delete("1.0", tk.END)
        self.status_label.config(text="🐶思考中...")
        self.processing = True

        # 显示“正在输入...”指示器
        self.typing_frame = self._add_typing_indicator()

        # 后台线程流式获取回复
        thread = threading.Thread(target=self._process_agent_stream, args=(user_text,))
        thread.daemon = True
        thread.start()

    def _process_agent_stream(self, user_text):
        try:
            logger.info(f"用户输入: {user_text}")
            full_response = ""
            first_token = True
            for token in self.agent.chat_stream(user_text):
                if first_token:
                    self.root.after(0, self._remove_typing_indicator)
                    first_token = False
                full_response += token
                self.root.after(0, self._update_agent_message, full_response)

            if first_token:   # 没有收到任何 token
                self.root.after(0, self._remove_typing_indicator)
                self.root.after(0, self._add_agent_message, "（无内容）")
            else:
                self.root.after(0, self._finish_stream, full_response)
            logger.info("Agent 回复完成")
        except Exception as e:
            logger.error(f"Agent 异常: {e}")
            self.root.after(0, self._remove_typing_indicator)
            self.root.after(0, self._add_system_message, f"❌ 错误: {e}")
        finally:
            self.processing = False
            self.root.after(0, lambda: self.status_label.config(text="就绪"))

    # ──────────────── 消息渲染 ────────────────
    def _add_message_frame(self, text, is_user=True):
        """添加一个完整消息气泡，并返回其 Frame 对象"""
        bubble_bg = USER_BUBBLE if is_user else AGENT_BUBBLE
        align_side = tk.RIGHT if is_user else tk.LEFT
        anchor_val = "e" if is_user else "w"
        avatar_text = "🍕" if is_user else "🥑"
        username = "BingGo" if is_user else "DoTi"
        time_str = time.strftime("%H:%M")

        # 外层容器（用于对齐）
        outer = tk.Frame(self.msg_frame, bg=BG_CHAT)
        outer.pack(fill=tk.X, padx=16, pady=(4, 1))

        # 内层气泡容器
        bubble_frame = tk.Frame(outer, bg=bubble_bg, padx=10, pady=6)
        bubble_frame.pack(side=align_side, anchor=anchor_val, padx=4)

        # 头像和用户名行
        header = tk.Frame(bubble_frame, bg=bubble_bg)
        header.pack(anchor="w", fill=tk.X)
        tk.Label(header, text=avatar_text, font=("Segoe UI", 12), bg=bubble_bg, fg=FG).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(header, text=username, font=FONT_BOLD, bg=bubble_bg, fg=ACCENT_GREEN if not is_user else ACCENT_BLURPLE).pack(side=tk.LEFT)
        tk.Label(header, text=time_str, font=FONT_SMALL, bg=bubble_bg, fg=FG_SECONDARY).pack(side=tk.RIGHT)

        # 消息文本
        msg_label = tk.Label(bubble_frame, text=text, font=FONT, bg=bubble_bg, fg=FG,
                             justify=tk.LEFT, wraplength=400, anchor="w")
        msg_label.pack(anchor="w", pady=(4, 0))

        # 自动滚动到底部
        self.canvas.yview_moveto(1.0)
        return outer

    def _add_user_message(self, text):
        self._add_message_frame(text, is_user=True)

    def _add_agent_message(self, text):
        self._add_message_frame(text, is_user=False)

    def _update_agent_message(self, new_text):
        """流式更新：替换最后一个 Agent 消息的气泡"""
        # 找到最后一个 Agent 气泡并更新文本
        # 简便方法：删除最后一个消息帧（如果它是 Agent 的），然后新增
        # 注意：由于我们使用 pack，最后一个子组件就是最后的消息
        children = self.msg_frame.winfo_children()
        if children:
            last = children[-1]
            # 判断是否是我们创建的 Agent 消息（通过背景色识别，简易起见用标记）
            # 这里我们用一个属性记录当前流式更新的目标帧
            if hasattr(self, '_stream_target') and self._stream_target in children:
                self._stream_target.destroy()
        # 创建新的 Agent 消息气泡
        self._stream_target = self._add_message_frame(new_text, is_user=False)

    def _finish_stream(self, final_text):
        """流式结束后的清理（如果有保存的临时引用）"""
        if hasattr(self, '_stream_target'):
            del self._stream_target

    def _add_typing_indicator(self):
        """显示正在输入指示器并返回 Frame"""
        frame = tk.Frame(self.msg_frame, bg=BG_CHAT)
        frame.pack(fill=tk.X, padx=16, pady=(4, 2))
        lbl = tk.Label(frame, text="🥑 正在输入...", font=FONT_SMALL, fg=FG_SECONDARY, bg=BG_CHAT)
        lbl.pack(side=tk.LEFT, padx=(4, 0))
        self.canvas.yview_moveto(1.0)
        return frame

    def _remove_typing_indicator(self):
        if hasattr(self, 'typing_frame') and self.typing_frame:
            self.typing_frame.destroy()
            self.typing_frame = None

    def _add_system_message(self, text):
        """居中灰色系统消息"""
        frame = tk.Frame(self.msg_frame, bg=BG_CHAT)
        frame.pack(fill=tk.X, padx=16, pady=4)
        tk.Label(frame, text=text, font=FONT_SMALL, fg=FG_SECONDARY, bg=BG_CHAT, anchor="center").pack(fill=tk.X)
        self.canvas.yview_moveto(1.0)

    # ──────────────── 功能按钮 ────────────────
    def clear_chat(self):
        if self.processing:
            messagebox.showwarning("提示", "请等待当前对话完成后再清空。")
            return
        self.agent.memory.clear()
        for widget in self.msg_frame.winfo_children():
            widget.destroy()
        self._add_system_message("对话已清空。")
        logger.info("对话已清空")

    def export_chat(self):
        # 收集所有气泡中的文本
        lines = []
        for child in self.msg_frame.winfo_children():
            self._collect_text(child, lines)
        content = "\n".join(lines)
        if not content.strip():
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("文本文件", "*.txt")],
                                                 title="导出对话记录")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self._add_system_message(f"✅ 已导出至📁: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def _collect_text(self, widget, lines):
        if isinstance(widget, tk.Label):
            text = widget.cget("text")
            if text:
                lines.append(text)
        for child in widget.winfo_children():
            self._collect_text(child, lines)

    def on_closing(self):
        logger.info("桌面程序关闭")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopChatApp(root)
    root.mainloop()