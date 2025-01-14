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
                is_detailed = i < 3

                result_box = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=180 if is_detailed else 80,
                    spacing=15,
                    padding=[20, 10]
                )

                with result_box.canvas.before:
                    Color(0.15, 0.15, 0.15, 1)
                    Rectangle(pos=result_box.pos, size=result_box.size)

                content_box = BoxLayout(
                    orientation='vertical',
                    size_hint_x=0.85,
                    spacing=5
                )

                title = node['title']
                if len(title) > 60:
                    title = title[:57] + '...'

                title_label = Label(
                    text=title,
                    size_hint_y=None,
                    height=30,
                    halign='left',
                    valign='middle',
                    bold=True,
                    font_size='16sp',
                    color=(0.95, 0.95, 0.95, 1),
                    text_size=(None, 30)
                )
                content_box.add_widget(title_label)

                if is_detailed:
                    try:
                        detailed_info = self.tracker.get_manga_details(node['id'])

                        stats_box = BoxLayout(
                            orientation='horizontal',
                            size_hint_y=None,
                            height=30,
                            spacing=15
                        )

                        stats = [
                            (f"Ch: {detailed_info.get('num_chapters', '?')}", (0.8, 0.8, 0.8, 1)),
                            (f"Score: {detailed_info.get('mean', 'N/A')}", (1, 0.8, 0.2, 1)),
                            (f"Year: {detailed_info.get('start_date', '')[:4] if detailed_info.get('start_date') else 'N/A'}", (0.8, 0.8, 0.8, 1)),
                            (f"Status: {detailed_info.get('status', 'Unknown').replace('_', ' ').title()}", (0.6, 0.8, 1, 1))
                        ]

                        for text, color in stats:
                            stat_label = Label(
                                text=text,
                                color=color,
                                font_size='14sp',
                                size_hint_x=0.25,
                                halign='left',
                                text_size=(None, 30)
                            )
                            stats_box.add_widget(stat_label)

                        content_box.add_widget(stats_box)

                        if detailed_info.get('synopsis'):
                            synopsis = detailed_info['synopsis']
                            if len(synopsis) > 150:
                                synopsis = synopsis[:150] + '...'

                            synopsis_label = Label(
                                text=synopsis,
                                size_hint_y=None,
                                height=80,
                                halign='left',
                                valign='top',
                                font_size='13sp',
                                color=(0.7, 0.7, 0.7, 1),
                                text_size=(800, 80)
                            )
                            content_box.add_widget(synopsis_label)

                    except Exception as e:
                        print(f"Failed to get details for manga {node['id']}: {e}")

                else:
                    basic_info_label = Label(
                        text="",
                        color=(0.7, 0.7, 0.7, 1),
                        font_size='14sp',
                        halign='left',
                        size_hint_y=None,
                        height=30,
                        text_size=(None, 30)
                    )
                    content_box.add_widget(basic_info_label)

                result_box.add_widget(content_box)

                button_box = BoxLayout(
                    orientation='vertical',
                    size_hint_x=0.15,
                    padding=[0, (result_box.height - 40) / 2]
                )

                select_btn = Button(
                    text='Select',
                    size_hint_y=None,
                    height=40,
                    background_normal='',
                    background_color=(0.2, 0.6, 0.9, 1),
                    color=(1, 1, 1, 1),
                    font_size='15sp'
                )
                select_btn.bind(
                    on_release=lambda btn, m=node: self.select_manga(m)
                )
                button_box.add_widget(select_btn)
                result_box.add_widget(button_box)

                self.results_list.add_widget(result_box)
                self.results_list.add_widget(Widget(size_hint_y=None, height=10))

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
        content = BoxLayout(orientation='vertical', spacing=15, padding=[25, 25])

        with content.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            Rectangle(pos=content.pos, size=content.size)

        scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint=(1, 1)
        )

        main_layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        title_label = Label(
            text=self.manga_card.title,
            size_hint_y=None,
            height=40,
            halign='left',
            valign='middle',
            bold=True,
            font_size='18sp',
            color=(0.95, 0.95, 0.95, 1)
        )
        main_layout.add_widget(title_label)

        main_content = BoxLayout(
            orientation='horizontal',
            spacing=20,
            size_hint_y=None,
            height=400
        )

        image_box = BoxLayout(
            orientation='vertical',
            size_hint_x=0.3,
            size_hint_y=None,
            height=400,
            padding=[0, 0, 20, 0]
        )

        with image_box.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=image_box.pos, size=image_box.size)

        if hasattr(self.manga_card, 'thumbnail_url') and self.manga_card.thumbnail_url:
            image = AsyncImage(
                source=self.manga_card.thumbnail_url,
                allow_stretch=True,
                keep_ratio=True
            )
            image_box.add_widget(image)

        main_content.add_widget(image_box)

        details_box = BoxLayout(
            orientation='vertical',
            spacing=20,
            padding=[20, 20],
            size_hint_x=0.7,
            size_hint_y=None,
            height=400
        )

        with details_box.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=details_box.pos, size=details_box.size)

        status_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=90,
            spacing=10
        )

        status_label = Label(
            text='Status',
            size_hint_y=None,
            height=30,
            halign='left',
            color=(0.7, 0.7, 0.7, 1),
            font_size='16sp',
            text_size=(None, 30)
        )
        status_spinner = Spinner(
            text=self.manga_card.tracking_status,
            values=['Reading', 'Completed', 'On Hold', 'Dropped', 'Plan to Read'],
            size_hint_y=None,
            height=50,
            background_normal='',
            background_color=(0.2, 0.2, 0.2, 1),
            color=(0.9, 0.9, 0.9, 1)
        )
        status_section.add_widget(status_label)
        status_section.add_widget(status_spinner)

        chapters_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=90,
            spacing=10
        )

        chapters_label = Label(
            text='Chapters Read',
            size_hint_y=None,
            height=30,
            halign='left',
            color=(0.7, 0.7, 0.7, 1),
            font_size='16sp',
            text_size=(None, 30)
        )
        chapters_input = TextInput(
            text=self.manga_card.chapter_text.split('/')[0] if '/' in self.manga_card.chapter_text else '0',
            multiline=False,
            size_hint_y=None,
            height=50,
            input_filter='int',
            background_normal='',
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            padding=[15, 12],
            font_size='16sp'
        )
        chapters_section.add_widget(chapters_label)
        chapters_section.add_widget(chapters_input)

        score_section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=90,
            spacing=10
        )

        score_label = Label(
            text='Score',
            size_hint_y=None,
            height=30,
            halign='left',
            color=(0.7, 0.7, 0.7, 1),
            font_size='16sp',
            text_size=(None, 30)
        )
        score_spinner = Spinner(
            text='Score',
            values=[str(i) for i in range(11)],
            size_hint_y=None,
            height=50,
            background_normal='',
            background_color=(0.2, 0.2, 0.2, 1),
            color=(0.9, 0.9, 0.9, 1)
        )
        score_section.add_widget(score_label)
        score_section.add_widget(score_spinner)

        for section in [status_section, chapters_section, score_section]:
            details_box.add_widget(section)

        main_content.add_widget(details_box)
        main_layout.add_widget(main_content)

        save_btn = Button(
            text='Save Changes',
            size_hint_y=None,
            height=50,
            background_normal='',
            background_color=(0.2, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        save_btn.bind(on_release=lambda x: self.save_changes(
            status_spinner.text,
            chapters_input.text,
            score_spinner.text
        ))

        button_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=70,
            padding=[20, 10]
        )
        button_box.add_widget(save_btn)
        main_layout.add_widget(button_box)

        scroll_view.add_widget(main_layout)
        content.add_widget(scroll_view)
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
            manga_details = self.tracker.get_manga_details(self.manga_id)
            total_chapters = manga_details.get('num_chapters', '?')

            self.tracker.update_manga_list_status(
                manga_id=self.manga_id,
                status=status.lower().replace(' ', '_'),
                num_chapters_read=int(chapters) if chapters else None,
                score=int(score) if score != 'Score' else None
            )

            self.manga_card.tracking_status = status
            self.manga_card.chapter_text = f"{chapters}/{total_chapters}"

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