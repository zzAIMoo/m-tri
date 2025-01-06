from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, BooleanProperty, ObjectProperty, NumericProperty
from .manga_details import MangaDetailsPopup
from kivy.core.image import Image as CoreImage
from kivy.loader import Loader
from functools import partial
from kivy.clock import Clock
from urllib.parse import quote

class MangaCard(BoxLayout):
    title = StringProperty('')
    tracking_status = StringProperty('')
    mihon_status = StringProperty('')
    chapter_text = StringProperty('')
    status_color = ListProperty([0, 0, 0, 0])
    thumbnail_url = StringProperty('')
    url = StringProperty('')
    is_nsfw = BooleanProperty(False)
    categories = ListProperty([])
    mal_id = NumericProperty(0)
    tracker = ObjectProperty(None)
    show_thumbnail = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.status_colors = {
            'Reading': [0.2, 0.6, 0.2, 1],
            'Completed': [0.2, 0.4, 0.8, 1],
            'On Hold': [0.8, 0.6, 0.2, 1],
            'Dropped': [0.8, 0.2, 0.2, 1],
            'Plan to Read': [0.4, 0.4, 0.4, 1],
            'Untracked': [0.3, 0.3, 0.3, 1]
        }
        self.mal_id = int(kwargs.get('mal_id', 0))
        super().__init__(**kwargs)
        self.status_color = self.status_colors.get(self.tracking_status, self.status_colors['Untracked'])
        if self.show_thumbnail:
            Clock.schedule_once(lambda dt: self.preload_image(), 0)

    def on_tracking_status(self, instance, value):
        self.status_color = self.status_colors.get(value, self.status_colors['Untracked'])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            popup = MangaDetailsPopup(self, self.tracker, self.mal_id)
            popup.open()
            return True
        return super().on_touch_down(touch)

    def preload_image(self):
        if self.thumbnail_url:
            clean_url = self.thumbnail_url.split(' ')[0]
            encoded_url = quote(clean_url, safe=':/?=&')
            Loader.max_upload_per_frame = 8
            proxyImage = Loader.image(encoded_url)
            proxyImage.bind(on_load=self._image_loaded)

    def _image_loaded(self, proxyImage):
        if proxyImage.image.texture:
            pass