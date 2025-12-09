from src.view.window import *
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
    print(dp_settings.get_all())
