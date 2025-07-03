from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

class SpriteToolsApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        btn1 = Button(text='Generar Spritesheet')
        btn2 = Button(text='Extraer Frames')
        btn1.bind(on_press=lambda x: self.run_script('Sprite múltiple+truco v5.py'))
        btn2.bind(on_press=lambda x: self.run_script('sprite a frame v5 Mejorado.py'))
        layout.add_widget(btn1)
        layout.add_widget(btn2)
        return layout

    def run_script(self, script_name):
        print(f"Ejecutando {script_name}...")
        # Aquí iría el código para llamar a tus scripts

if __name__ == "__main__":
    SpriteToolsApp().run()
