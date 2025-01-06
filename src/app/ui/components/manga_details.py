from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.app import App
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from kivy.uix.image import AsyncImage
from kivy.uix.gridlayout import GridLayout

class MangaDetailsPopup(Popup):
    search_query = StringProperty('')

    def __init__(self, manga_card, tracker, manga_id, **kwargs):
        super().__init__(**kwargs)
        self.manga_card = manga_card
        self.tracker = tracker
        self.manga_id = manga_id
        self.title = manga_card.title
        self.size_hint = (0.8, 0.8)
        self.search_query = manga_card.title

        app = App.get_running_app()
        tracker_importer = app.root
        tracker_importer.selected_manga_title = manga_card.title
        tracker_importer.selected_manga_url = manga_card.url

        if manga_card.tracking_status != "Untracked":
            self.show_tracked_manga()
        else:
            self.show_search_results()

    def search(self, query):
        self.search_query = query
        self.search_mal()

    def show_search_results(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        search_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=40,
            spacing=10
        )

        search_input = TextInput(
            text=self.search_query,
            multiline=False,
            size_hint_x=0.8,
            height=40
        )
        search_input.bind(
            on_text_validate=lambda instance: self.search_mal(instance.text)
        )

        search_button = Button(
            text='Search',
            size_hint_x=0.2,
            height=40
        )
        search_button.bind(
            on_release=lambda instance: self.search_mal(search_input.text)
        )

        search_box.add_widget(search_input)
        search_box.add_widget(search_button)
        content.add_widget(search_box)

        scroll = ScrollView(
            size_hint_y=1,
            do_scroll_x=False,
            do_scroll_y=True
        )

        self.results_list = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_y=None
        )
        self.results_list.bind(minimum_height=self.results_list.setter('height'))

        loading_label = Label(
            text='Searching MyAnimeList...',
            size_hint_y=None,
            height=40
        )
        self.results_list.add_widget(loading_label)

        scroll.add_widget(self.results_list)
        content.add_widget(scroll)
        self.content = content

        self.search_mal(self.manga_card.title)

    def create_cover_image(self, image_url):
        cover_box = BoxLayout(
            size_hint=(None, None),
            size=(80, 120),
            padding=[0, 0, 10, 0]
        )

        with cover_box.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=cover_box.pos, size=cover_box.size)

        loading_label = Label(
            text='Loading...',
            size_hint=(1, 1),
            color=(0.7, 0.7, 0.7, 1)
        )
        cover_box.add_widget(loading_label)

        if not image_url.startswith('http'):
            image_url = f'https:{image_url}'

        cover_image = AsyncImage(
            source=image_url,
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
            nocache=True
        )

        def on_load(*args):
            if cover_image.texture:
                if loading_label in cover_box.children:
                    cover_box.remove_widget(loading_label)
                    cover_box.add_widget(cover_image)
            else:
                loading_label.text = 'No image'

        cover_image.bind(texture=on_load)
        return cover_box

    def search_mal(self, query):
        try:
            self.search_query = query
            results = self.tracker.search_manga(query)
            self.results_list.clear_widgets()

            if not results or 'data' not in results:
                self.results_list.add_widget(
                    Label(
                        text='No results found',
                        size_hint_y=None,
                        height=40
                    )
                )
                return

            for i, manga in enumerate(results['data']):
                node = manga['node']

                detailed_info = None
                if i < 3:
                    try:
                        detailed_info = self.tracker.get_manga_details(node['id'])
                    except Exception as e:
                        print(f"Failed to get details for manga {node['id']}: {e}")

                result_box = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=180 if detailed_info else 100,
                    spacing=15,
                    padding=[20, 10]
                )

                with result_box.canvas.before:
                    Color(0.15, 0.15, 0.15, 1)
                    Rectangle(pos=result_box.pos, size=result_box.size)

                info_box = BoxLayout(
                    orientation='vertical',
                    size_hint_x=0.85,
                    spacing=8,
                    padding=[15, 5, 15, 5]
                )

                title = node['title']
                if len(title) > 60:
                    title = title[:57] + '...'

                title_label = Label(
                    text=title,
                    text_size=(None, 30),
                    size_hint_y=None,
                    height=30,
                    halign='left',
                    valign='middle',
                    bold=True,
                    font_size='16sp',
                    color=(0.95, 0.95, 0.95, 1),
                    shorten=True,
                    shorten_from='right',
                    padding=(0, 0)
                )
                info_box.add_widget(title_label)

                if detailed_info:
                    details_box = BoxLayout(
                        orientation='vertical',
                        size_hint_y=None,
                        height=100,
                        spacing=5
                    )

                    stats_grid = GridLayout(
                        cols=2,
                        size_hint_y=None,
                        height=50,
                        spacing=[20, 5],
                        padding=[0, 5]
                    )

                    stats = [
                        ('»', f"{detailed_info.get('num_chapters', '?')} ch"),
                        ('»', f"{detailed_info.get('mean', 'N/A')}"),
                        ('»', detailed_info.get('start_date', '')[:4] if detailed_info.get('start_date') else 'N/A'),
                        ('»', detailed_info.get('status', 'Unknown').replace('_', ' ').title())
                    ]

                    for icon, value in stats:
                        stat_box = BoxLayout(
                            orientation='horizontal',
                            size_hint_y=None,
                            height=20,
                            spacing=5
                        )

                        icon_label = Label(
                            text=icon,
                            size_hint_x=None,
                            width=25,
                            color=(0.6, 0.8, 1, 1),
                            font_size='14sp'
                        )

                        value_label = Label(
                            text=value,
                            color=(0.8, 0.8, 0.8, 1),
                            font_size='14sp',
                            halign='left',
                            text_size=(None, None)
                        )

                        stat_box.add_widget(icon_label)
                        stat_box.add_widget(value_label)
                        stats_grid.add_widget(stat_box)

                    details_box.add_widget(stats_grid)

                    if detailed_info.get('synopsis'):
                        synopsis = detailed_info['synopsis']
                        if len(synopsis) > 120:
                            synopsis = synopsis[:120] + '...'

                        synopsis_label = Label(
                            text=synopsis,
                            text_size=(None, None),
                            size_hint_y=None,
                            height=40,
                            halign='left',
                            valign='top',
                            font_size='13sp',
                            color=(0.6, 0.6, 0.6, 1)
                        )
                        details_box.add_widget(synopsis_label)

                    info_box.add_widget(details_box)
                else:
                    details = f"≣ {node.get('num_chapters', '?')} chapters"
                    details_label = Label(
                        text=details,
                        size_hint_y=None,
                        height=30,
                        halign='left',
                        font_size='14sp',
                        color=(0.7, 0.7, 0.7, 1)
                    )
                    info_box.add_widget(details_label)

                result_box.add_widget(info_box)

                select_btn = Button(
                    text='Select',
                    size_hint=(0.12, 0.6),
                    pos_hint={'center_y': 0.5},
                    background_normal='',
                    background_color=(0.2, 0.6, 0.9, 1),
                    color=(1, 1, 1, 1),
                    font_size='15sp'
                )
                select_btn.bind(
                    on_release=lambda btn, m=node: self.select_manga(m)
                )
                result_box.add_widget(select_btn)

                self.results_list.add_widget(result_box)

                margin = Widget(size_hint_y=None, height=10)
                self.results_list.add_widget(margin)

        except Exception as e:
            self.results_list.clear_widgets()
            self.results_list.add_widget(
                Label(
                    text=f'Search failed: {str(e)}',
                    size_hint_y=None,
                    height=40
                )
            )

    def show_tracked_manga(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        status_spinner = Spinner(
            text=self.manga_card.tracking_status,
            values=['Reading', 'Completed', 'On Hold', 'Dropped', 'Plan to Read'],
            size_hint_y=None,
            height=40
        )

        chapters_input = TextInput(
            text=self.manga_card.chapter_text.split('/')[0] if '/' in self.manga_card.chapter_text else '0',
            multiline=False,
            size_hint_y=None,
            height=40,
            input_filter='int'
        )

        score_spinner = Spinner(
            text='Score',
            values=[str(i) for i in range(11)],
            size_hint_y=None,
            height=40
        )

        save_btn = Button(
            text='Save Changes',
            size_hint_y=None,
            height=40
        )
        save_btn.bind(on_release=lambda x: self.save_changes(
            status_spinner.text,
            chapters_input.text,
            score_spinner.text
        ))

        content.add_widget(Label(text='Status:', size_hint_y=None, height=30))
        content.add_widget(status_spinner)
        content.add_widget(Label(text='Chapters Read:', size_hint_y=None, height=30))
        content.add_widget(chapters_input)
        content.add_widget(Label(text='Score:', size_hint_y=None, height=30))
        content.add_widget(score_spinner)
        content.add_widget(Widget(size_hint_y=1))
        content.add_widget(save_btn)

        self.content = content

    def select_manga(self, manga_data):
        try:
            manga_id = manga_data['id']
            self.manga_id = manga_id
            self.tracker.add_manga(manga_id)
            self.manga_card.tracking_status = "Plan to Read"
            self.manga_card.mal_id = manga_id

            self.show_tracked_manga()

            app = App.get_running_app()
            tracker_importer = app.root
            if hasattr(tracker_importer, 'on_manga_matched'):
                tracker_importer.on_manga_matched(self.manga_card)

        except Exception as e:
            content = BoxLayout(orientation='vertical')
            content.add_widget(Label(text=f'Failed to add manga: {str(e)}'))
            self.content = content

    def save_changes(self, status, chapters, score):
        try:
            self.tracker.update_manga_list_status(
                manga_id=self.manga_id,
                status=status.lower().replace(' ', '_'),
                num_chapters_read=int(chapters) if chapters else None,
                score=int(score) if score != 'Score' else None
            )

            self.manga_card.tracking_status = status
            self.manga_card.chapter_text = f"{chapters}/?"

            app = App.get_running_app()
            tracker_importer = app.root
            tracker_importer.update_json_data(
                self.manga_id,
                status,
                chapters,
                score
            )

            self.dismiss()
        except Exception as e:
            print(f"Failed to save changes: {str(e)}")