from kivy.app import App
from kivy.uix.button import Button

class SpriteToolsApp(App):
    def build(self):
        return Button(text="¡SpriteTools APK! :v", size_hint=(0.5, 0.5))

if __name__ == "__main__":
    SpriteToolsApp().run()
