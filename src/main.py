from kivy.app import App
from kivy.core.window import Window
from app.ui.components.tracker_importer import TrackerImporter

class MihonTrackerApp(App):
    def build(self):
        Window.size = (1000, 600)
        return TrackerImporter()

def main():
    MihonTrackerApp().run()

if __name__ == "__main__":
    main()