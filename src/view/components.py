import customtkinter as ctk
import tkinter as tk
from tkinterdnd2 import DND_FILES
from tkinter import filedialog  # 引入標準的檔案選擇視窗

class FileDropFrame(ctk.CTkFrame):
    def __init__(self, master, on_drop_callback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.on_drop_callback = on_drop_callback

        # 設定外觀：灰色背景，有邊框
        self.configure(fg_color=("gray85", "gray25")) 
        self.configure(border_width=2, border_color="gray50")
        
        # 【新增】設定滑鼠游標為手指形狀，暗示可點擊
        self.configure(cursor="hand2")

        # 區域內的文字標籤
        self.label = ctk.CTkLabel(
            self, 
            text="點擊選擇檔案\n或將 CSV / XLSX 拖曳至此處",
            font=("Arial", 16)
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 【新增】雖然標籤在 Frame 上面，但標籤也要能被點擊
        # 否則使用者點到文字時會沒反應
        self.label.bind("<Button-1>", self.open_file_dialog)
        self.label.configure(cursor="hand2")

        # --- 註冊拖曳事件 ---
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<DragEnter>>", self.on_enter)
        self.dnd_bind("<<DragLeave>>", self.on_leave)
        self.dnd_bind("<<Drop>>", self.on_drop)
        
        # --- 【新增】註冊點擊事件 ---
        # <Button-1> 代表滑鼠左鍵點擊
        self.bind("<Button-1>", self.open_file_dialog)

    def on_enter(self, event):
        # 拖進來時變色
        self.configure(border_color="#3B8ED0", border_width=4)

    def on_leave(self, event):
        # 離開時恢復
        self.configure(border_color="gray50", border_width=2)

    def on_drop(self, event):
        # 放開檔案時
        self.configure(border_color="gray50", border_width=2)
        if event.data:
            # 處理 Windows 路徑可能的 {} 包裹問題
            file_path = event.data.strip("{}")
            self.on_drop_callback(file_path)

    def open_file_dialog(self, event=None):
        """
        【新增】開啟檔案選擇視窗
        """
        file_path = filedialog.askopenfilename(
            title="選擇資料檔案",
            filetypes=[
                ("Data Files", "*.csv *.xlsx"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx")
            ]
        )
        
        # 如果使用者有選擇檔案（沒有按取消）
        if file_path:
            self.on_drop_callback(file_path)


class CTkToolTip:
    """
    自定義的現代化 Tooltip 元件
    """
    def __init__(self, widget, text, delay=200):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        
        # 綁定事件
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.unschedule)
        self.widget.bind("<ButtonPress>", self.unschedule)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self, event=None):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
        self.hide()

    def show(self):
        if self.tooltip_window:
            return
        
        # 計算位置 (顯示在滑鼠下方偏右)
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # 建立漂浮視窗
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) # 移除視窗邊框
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # 設定樣式 (深色背景，白字)
        label = tk.Label(
            self.tooltip_window, 
            text=self.text, 
            justify='left',
            background="#1A1A1A", # 深灰底色
            foreground="#E0E0E0", # 淺灰文字
            relief='solid', 
            borderwidth=1,
            font=("Arial", 10),
            padx=8,
            pady=4
        )
        label.pack()

    def hide(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()