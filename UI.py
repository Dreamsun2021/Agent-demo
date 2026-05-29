import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from agent import Agent
from logger import logger
import customtkinter as ctk
from PIL import Image
# ========== 微信风格配色 ==========
BG_MAIN = "#F5F6F7"          # 主背景浅灰
BG_SIDEBAR = "#FFFFFF"       # 侧栏白色
BG_INPUT = "#FFFFFF"         # 输入框白色
FG = "#111111"               # 主要文字深灰
FG_SECONDARY = "#666666"     # 次要文字
ACCENT = "#5CB85C"           # 绿色强调（发送按钮、用户气泡）
USER_BUBBLE = "#9ED99E"      # 用户消息气泡绿色
AI_BUBBLE = "#EDEDED"        # AI消息气泡浅灰

# 滚动条颜色
SCROLLBAR_FG = "#DDDDDD"
SCROLLBAR_HOVER = "#CCCCCC"

FONT = ("Microsoft YaHei", 15)
FONT_BOLD = ("Microsoft YaHei", 15, "bold")
FONT_SMALL = ("Microsoft YaHei", 13)

# 设置为浅色模式
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class DesktopChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Agent")
        self.root.geometry("1000x650")
        self.root.minsize(800, 500)
        self.root.configure(bg=BG_MAIN)   # 根窗口背景

        self.agent = Agent()
        self.processing = False
        self._stream_target = None
        self.typing_frame = None

        # 加载头像图片（如果文件不存在则回退到 emoji）
        try:
            self.user_img = ctk.CTkImage(light_image=Image.open("user_avatar.png"), size=(56, 56))
        except:
            self.user_img = None
        try:
            self.ai_img = ctk.CTkImage(light_image=Image.open("ai_avatar.png"), size=(56, 56))
        except:
            self.ai_img = None

        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self.root, fg_color=BG_MAIN)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧边栏（白色）
        sidebar = ctk.CTkFrame(main_frame, fg_color=BG_SIDEBAR, width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="功能面板", font=FONT_BOLD, text_color=FG).pack(pady=30)
        ctk.CTkLabel(sidebar, text="待开发\n对话列表\n模型设置\n历史记录",
                     text_color=FG_SECONDARY, font=FONT_SMALL).pack(pady=5)

        sidebar_bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=12)

        self.clear_btn = ctk.CTkButton(
            sidebar_bottom, text="  🗑️  清空对话", font=FONT_SMALL,
            fg_color="#F0F0F0", hover_color="#E0E0E0",
            text_color=FG, corner_radius=20, height=36, anchor="w",
            command=self.clear_chat
        )
        self.clear_btn.pack(fill=tk.X, pady=6)

        self.export_btn = ctk.CTkButton(
            sidebar_bottom, text="  📎       导出记录", font=FONT_SMALL,
            fg_color="#F0F0F0", hover_color="#E0E0E0",
            text_color=FG, corner_radius=20, height=36, anchor="w",
            command=self.export_chat
        )
        self.export_btn.pack(fill=tk.X, pady=6)

        # 右侧聊天区
        chat_area = ctk.CTkFrame(main_frame, fg_color=BG_MAIN)
        chat_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        chat_container = ctk.CTkFrame(chat_area, fg_color=BG_MAIN)
        chat_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(chat_container, bg=BG_MAIN, highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(
            chat_container, orientation=tk.VERTICAL, command=self.canvas.yview,
            width=6, corner_radius=3, fg_color=SCROLLBAR_FG, button_color=SCROLLBAR_FG,
            button_hover_color=SCROLLBAR_HOVER
        )
        self.msg_frame = ctk.CTkFrame(self.canvas, fg_color=BG_MAIN)

        # 创建 canvas 内的窗口，保存其 id
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")

        # 当 canvas 尺寸改变时，同时更新 msg_frame 和 canvas 上窗口的宽度
        def on_canvas_configure(event):
            canvas_width = event.width
            self.msg_frame.configure(width=canvas_width)
            self.canvas.itemconfig(self.canvas_frame_id, width=canvas_width)

        self.canvas.bind("<Configure>", on_canvas_configure)

        self.msg_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 输入框区域
        input_frame = ctk.CTkFrame(chat_area, fg_color=BG_MAIN)   # 背景与聊天区一致
        input_frame.pack(fill=tk.X, padx=10, pady=8)

        # 输入框（白色背景）
        self.entry = ctk.CTkTextbox(
            input_frame, height=80, font=FONT,
            fg_color=BG_INPUT, text_color=FG,
            border_width=0, corner_radius=12, padx=12, pady=8
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=8)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", self._on_shift_enter)
        self.entry.focus()

        # 发送按钮（绿色）
        send_btn = ctk.CTkButton(
            input_frame, text="发送", font=FONT_BOLD,
            fg_color=ACCENT, hover_color="#238C32",
            text_color="white", corner_radius=12, width=80, height=36,
            command=self.send_message
        )
        send_btn.pack(side=tk.RIGHT, padx=8, pady=(0, 8))

        # 状态标签（灰色文字）
        self.status_label = ctk.CTkLabel(input_frame, text="就绪", font=FONT_SMALL, text_color=FG_SECONDARY)
        self.status_label.pack(side=tk.RIGHT, padx=10)

        self._add_system_message("欢迎使用 AI 助手！")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_enter(self, event):
        self.send_message()
        return "break"

    def _on_shift_enter(self, event):
        self.entry.insert(tk.INSERT, "\n")
        return "break"

    def send_message(self):
        if self.processing:
            messagebox.showwarning("提示", "正在生成回复，请稍候...")
            return
        user_text = self.entry.get("1.0", tk.END).strip()
        if not user_text:
            return

        self._add_user_message(user_text)
        self.entry.delete("1.0", tk.END)
        self.status_label.configure(text="思考中...")
        self.processing = True
        self.typing_frame = self._add_typing_indicator()

        thread = threading.Thread(target=self._process_agent_stream, args=(user_text,))
        thread.daemon = True
        thread.start()

    def _process_agent_stream(self, user_text):
        try:
            full_response = ""
            first_token = True
            for token in self.agent.chat_stream(user_text):
                if first_token:
                    self.root.after(0, self._remove_typing_indicator)
                    first_token = False
                full_response += token
                self.root.after(0, self._update_agent_message, full_response)

            if first_token:
                self.root.after(0, self._remove_typing_indicator)
                self.root.after(0, self._add_agent_message, "（无内容）")
            else:
                self.root.after(0, self._finish_stream)
        except Exception as e:
            self.root.after(0, self._remove_typing_indicator)
            self.root.after(0, self._add_system_message, f"错误：{str(e)}")
        finally:
            self.processing = False
            self.root.after(0, lambda: self.status_label.configure(text="就绪"))

    def _add_message_frame(self, text, is_user=True):
        avatar = "👤" if is_user else "🥑"
        name = "我" if is_user else "AI"
        time_str = time.strftime("%H:%M")

        # 外层容器：占满整行宽度
        msg_frame = ctk.CTkFrame(self.msg_frame, fg_color="transparent")
        msg_frame.pack(fill=tk.X, padx=0, pady=6)

        if is_user:
            # 用户消息：整体靠右
            left_spacer = ctk.CTkFrame(msg_frame, fg_color="transparent")
            left_spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)

            right_box = ctk.CTkFrame(msg_frame, fg_color="transparent")
            right_box.pack(side=tk.RIGHT,padx=(0,12))

            # 头像（放在气泡右侧）
            if self.user_img:
                avatar_label = ctk.CTkLabel(
                    right_box, image=self.user_img, text="", width=56, height=56,
                    fg_color="transparent"
                )
            else:
                avatar_label = ctk.CTkLabel(
                    right_box, text=avatar, width=56, height=56, corner_radius=18,
                    fg_color=USER_BUBBLE, text_color="white"
                )
            avatar_label.grid(row=0, column=1, padx=(4, 0), pady=2, sticky='n')


            # 气泡容器（绿色）
            bubble = ctk.CTkFrame(
                right_box,
                fg_color=USER_BUBBLE,
                corner_radius=16,
            )
            bubble.grid(row=0, column=0, padx=(0, 4), pady=2, sticky='n')

            # 头部（名字+时间）
            header = ctk.CTkFrame(bubble, fg_color="transparent")
            header.pack(fill=tk.X, padx=10, pady=2)
            ctk.CTkLabel(header, text=name, font=FONT_SMALL, text_color=FG).pack(side=tk.LEFT)
            ctk.CTkLabel(header, text=time_str, font=("Microsoft YaHei", 9), text_color=FG_SECONDARY).pack(
                side=tk.RIGHT)

            text_label = ctk.CTkLabel(
                bubble, text=text, font=FONT, text_color=FG,
                wraplength=460, justify=tk.LEFT
            )
            text_label.pack(padx=12, pady=(0, 8), anchor="w")
            text_label.is_message_content = True

        else:
            # AI 消息：左侧布局，气泡浅灰，文字深灰
            if self.ai_img:
                avatar_label = ctk.CTkLabel(
                    msg_frame, image=self.ai_img, text="", width=56, height=56,
                    fg_color="transparent"
                )
            else:
                avatar_label = ctk.CTkLabel(
                    msg_frame, text=avatar, width=56, height=56, corner_radius=18,
                    fg_color=AI_BUBBLE, text_color=FG
                )
            avatar_label.pack(side=tk.LEFT, padx=4, anchor='n')

            bubble = ctk.CTkFrame(
                msg_frame,
                fg_color=AI_BUBBLE,
                corner_radius=16,
            )
            bubble.pack(side=tk.LEFT, anchor="n", padx=(4, 10))

            header = ctk.CTkFrame(bubble, fg_color="transparent")
            header.pack(fill=tk.X, padx=10, pady=2)
            ctk.CTkLabel(header, text=name, font=FONT_SMALL, text_color=FG).pack(side=tk.LEFT)
            ctk.CTkLabel(header, text=time_str, font=("Microsoft YaHei", 9), text_color=FG_SECONDARY).pack(side=tk.RIGHT)

            text_label = ctk.CTkLabel(
                bubble, text=text, font=FONT, text_color=FG,
                wraplength=460, justify=tk.LEFT
            )
            text_label.pack(padx=12, pady=(0, 8), anchor="w")
            text_label.is_message_content = True

        # 滚动到底部
        self.root.after(10, lambda: self.canvas.yview_moveto(1.0))
        return msg_frame

    def _add_user_message(self, text):
        self._add_message_frame(text, is_user=True)

    def _add_agent_message(self, text):
        self._add_message_frame(text, is_user=False)

    def _update_agent_message(self, new_text):
        children = self.msg_frame.winfo_children()
        if children and hasattr(self, '_stream_target') and self._stream_target in children:
            self._stream_target.destroy()
        self._stream_target = self._add_message_frame(new_text, is_user=False)

    def _finish_stream(self):
        if hasattr(self, '_stream_target'):
            del self._stream_target

    def _add_typing_indicator(self):
        frame = ctk.CTkFrame(self.msg_frame, fg_color="transparent")
        frame.pack(fill=tk.X, padx=16, pady=6)
        ctk.CTkLabel(frame, text="🥑 正在输入...", text_color=FG_SECONDARY).pack(side=tk.LEFT)
        self.canvas.yview_moveto(1.0)
        return frame

    def _remove_typing_indicator(self):
        if hasattr(self, 'typing_frame') and self.typing_frame:
            self.typing_frame.destroy()

    def _add_system_message(self, text):
        frame = ctk.CTkFrame(self.msg_frame, fg_color="transparent")
        frame.pack(fill=tk.X, pady=6)
        ctk.CTkLabel(frame, text=text, text_color=FG_SECONDARY).pack(anchor="center")
        self.canvas.yview_moveto(1.0)

    def clear_chat(self):
        if self.processing:
            messagebox.showwarning("提示", "请等待当前对话完成")
            return
        self.agent.memory.clear()
        for w in self.msg_frame.winfo_children():
            w.destroy()
        self._add_system_message("对话已清空")

    def export_chat(self):
        def collect_texts(widget, result):
            for child in widget.winfo_children():
                if hasattr(child, 'is_message_content') and child.is_message_content:
                    text = child.cget("text")
                    if text:
                        result.append(text)
                collect_texts(child, result)

        lines = []
        collect_texts(self.msg_frame, lines)

        if not lines:
            messagebox.showinfo("提示", "没有可导出的聊天记录")
            return

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(lines))
            self._add_system_message("✅ 导出成功")

    def on_closing(self):
        self.root.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    app = DesktopChatApp(root)
    root.mainloop()