from kivy.app import App
from kivy.uix.label import Label

class DemoApp(App):
    def build(self):
        return Label(text="Kivy is running on Android!", font_size=24)

if __name__ == "__main__":
    DemoApp().run()
