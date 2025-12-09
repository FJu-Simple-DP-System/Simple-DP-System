import customtkinter as ctk

class StartScreen(ctk.CTkFrame):
    def __init__(self, master, on_start_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_start_callback = on_start_callback
        
        # 設定背景色 (深色模式下稍微深一點)
        self.configure(fg_color=("gray95", "gray10"))

        # 使用 place 佈局讓內容置中
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # 1. 專題題目
        self.lbl_topic = ctk.CTkLabel(
            self.center_frame, 
            text="隱私強化技術應用之研究", 
            font=("Arial", 16),
            text_color="gray"
        )
        self.lbl_topic.pack(pady=(0, 10))

        # 2. 系統名稱 (大標題)
        self.lbl_title = ctk.CTkLabel(
            self.center_frame, 
            text="簡單差分隱私系統", 
            font=("Arial", 36, "bold"),
            text_color=("#3B8ED0", "#3B8ED0") # 藍色強調
        )
        self.lbl_title.pack(pady=(0, 5))
        
        self.lbl_subtitle = ctk.CTkLabel(
            self.center_frame, 
            text="Simple Differential Privacy System", 
            font=("Arial", 14, "italic")
        )
        self.lbl_subtitle.pack(pady=(0, 40))

        # 3. 開始按鈕
        self.btn_start = ctk.CTkButton(
            self.center_frame, 
            text="開始使用", 
            font=("Arial", 18, "bold"),
            height=50, 
            width=200,
            corner_radius=25,
            command=self.start_app
        )
        self.btn_start.pack(pady=(0, 40))

        # 4. 團隊資訊 (頁腳)
        self.footer_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.footer_frame.pack()

        team_info = "輔仁大學 人工智慧與資訊安全學士學位學程\n資安三專題實作 第13組"
        self.lbl_team = ctk.CTkLabel(
            self.footer_frame, 
            text=team_info, 
            font=("Arial", 12),
            text_color="gray50"
        )
        self.lbl_team.pack()

    def start_app(self):
        """按下按鈕後的動畫或轉場"""
        # 可以在這裡加一點 Loading 動畫，目前先直接呼叫 callback
        self.on_start_callback()