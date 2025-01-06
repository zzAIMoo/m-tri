from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, BooleanProperty, ObjectProperty, NumericProperty
from typing import Dict, Optional
from pathlib import Path
import json
from functools import partial
from core.auth.mal_auth import MALAuth, MALAuthWebView
from core.trackers.mal_tracker import MALMangaTracker
from app.config import MAL_CLIENT_ID, MAL_CLIENT_SECRET, CONFIG_FILE
from .manga_card import MangaCard
from .matching_popup import MangaMatchingPopup

Builder.load_file('src/app/ui/kv/tracker_importer.kv')

class TrackerImporter(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_tracker: Optional[str] = None
        self.manga_entries: Dict = {}
        self.tracker = None
        self.manga_cards = []
        self.categories = {}
        self.config_file = CONFIG_FILE
        self.show_thumbnails = False

        self.mal_auth = MALAuth(client_id=MAL_CLIENT_ID, client_secret=MAL_CLIENT_SECRET)

        if self.mal_auth.access_token:
            self.tracker = MALMangaTracker(self.mal_auth.access_token)
            self.ids.welcome_label.text = "Successfully logged in to MyAnimeList!"
            self.ids.import_button.disabled = False

        self.setup_trackers()
        self.setup_sorting()
        self.load_config()

    def setup_trackers(self):
        """Initialize available trackers"""
        trackers = [
            ("MAL", "mal", True),
            ("AniList", "anilist", False),
            ("Kitsu", "kitsu", False),
            ("MangaUpdates", "mu", False),
            ("Shikimori", "shiki", False),
            ("Bangumi", "bangumi", False),
        ]

        for name, key, implemented in trackers:
            btn = Button(
                text=name,
                size_hint_y=None,
                height=50,
                disabled=not implemented,
                background_color=(0.3, 0.3, 0.3, 1) if implemented else (0.2, 0.2, 0.2, 1)
            )
            btn.bind(on_release=lambda x, k=key: self.select_tracker(k))
            self.ids.tracker_list.add_widget(btn)

    def setup_sorting(self):
        """Setup sorting controls"""
        self.sort_states = {
            'title': False,
            'tracking_status': False,
            'mihon_status': False
        }

        sorting_box = BoxLayout(
            size_hint_y=None,
            height=40,
            spacing=20,
            padding=[20, 0]
        )

        sort_buttons = [
            ('Title', 'title'),
            ('Tracking Status', 'tracking_status'),
            ('Mihon Status', 'mihon_status')
        ]

        for text, key in sort_buttons:
            btn = Button(
                text=f'Sort by {text} ▼',
                size_hint_x=1,
                size_hint_y=None,
                height=40,
                font_name='DejaVuSans'
            )
            btn.bind(on_release=partial(self.sort_manga_list, key))
            sorting_box.add_widget(btn)

        self.ids.manga_list.parent.parent.add_widget(sorting_box, index=1)

    def load_config(self):
        """Load previous configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    last_file = config.get('last_loaded_file')
                    if last_file and Path(last_file).exists():
                        with open(last_file, 'r') as manga_file:
                            self.manga_entries = json.load(manga_file)
                            self.last_loaded_file = last_file
                            self.process_manga_entries()
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self, file_path):
        """Save current configuration"""
        try:
            config = {
                'last_loaded_file': str(file_path)
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {str(e)}")

    def select_tracker(self, tracker: str):
        """Handle tracker selection"""
        self.current_tracker = tracker
        self.ids.welcome_label.text = f"Selected Tracker: {tracker.upper()}"

        if tracker == "mal":
            self.ids.token_input.opacity = 0
            self.ids.login_button.text = "Login with MyAnimeList"
        else:
            self.ids.token_input.opacity = 1
            self.ids.login_button.text = "Login"

        self.ids.login_frame.opacity = 1

    def login(self):
        """Handle login process"""
        if self.current_tracker == "mal":
            def handle_auth_complete(auth_code):
                try:
                    access_token, refresh_token = self.mal_auth.get_tokens(auth_code)
                    self.handle_login_success(access_token)
                except Exception as e:
                    self.ids.welcome_label.text = f"Login failed: {str(e)}"

            auth_url = self.mal_auth.get_auth_url()
            auth_view = MALAuthWebView(
                auth_url=auth_url,
                on_auth_complete=handle_auth_complete
            )
            auth_view.open()
        else:
            token = self.ids.token_input.text
            if token:
                self.handle_login_success(token)

    def handle_login_success(self, token):
        """Handle successful login"""
        if self.current_tracker == "mal":
            self.tracker = MALMangaTracker(token)
            self.ids.welcome_label.text = "Successfully logged in to MyAnimeList!"

        self.ids.import_button.disabled = False

    def import_file(self):
        """Handle file import"""
        def load(selection):
            if selection:
                file_path = selection[0]
                try:
                    with open(file_path, 'r') as f:
                        self.manga_entries = json.load(f)

                    self.last_loaded_file = file_path
                    self.save_config(file_path)
                    self.process_manga_entries()

                except Exception as e:
                    print(f"Error loading file: {str(e)}")
                    self.ids.welcome_label.text = f"Error loading file: {str(e)}"
                finally:
                    popup.dismiss()

        file_chooser = FileChooserListView(
            filters=['*.tachibk', '*.json'],
            path='.'
        )
        file_chooser.bind(on_submit=lambda instance, selection, *args: load(selection))

        popup = Popup(
            title='Choose a backup file',
            content=file_chooser,
            size_hint=(0.9, 0.9)
        )
        popup.open()

    def process_manga_entries(self):
        """Process loaded manga entries"""
        self.categories = {str(i): cat["name"]
            for i, cat in enumerate(self.manga_entries.get('backupCategories', []))}
        self.categories['all'] = 'All Categories'

        category_values = [self.categories[k] for k in sorted(self.categories.keys())]
        self.ids.category_filter.values = category_values
        self.ids.category_filter.text = self.categories['all']

        max_width = max(
            self.ids.category_filter.font_size * len(cat)
            for cat in category_values
        )
        self.ids.category_filter.width = min(max(max_width + 50, 250), 500)

        self.update_manga_list()

    def create_manga_card(self, manga):
        """Create a manga card from manga data"""
        self.selected_manga_title = manga.get("title", "Unknown Title")

        tracking = manga.get("tracking", [])
        mal_tracking = next((t for t in tracking if t.get("syncId") == 1), None)

        title = manga.get("title", "Unknown Title")
        thumbnail_url = manga.get("thumbnailUrl", "")

        if mal_tracking:
            total_chapters = mal_tracking.get("totalChapters", "?")
            read_chapters = mal_tracking.get("lastChapterRead", 0)
            tracking_id = mal_tracking.get("mediaId", 0)
        else:
            total_chapters = len(manga.get("chapters", []))
            read_chapters = self.get_read_chapters(manga)
            tracking_id = 0

        if read_chapters == 0:
            mihon_status = "Unread"
        elif read_chapters == total_chapters and total_chapters != "?":
            mihon_status = "Completed"
        else:
            mihon_status = "Started"

        chapter_text = f"{read_chapters}/{total_chapters}"

        if mal_tracking:
            status_map = {
                1: "Reading",
                2: "Completed",
                3: "On Hold",
                4: "Dropped",
                5: "Plan to Read",
                6: "Plan to Read"
            }
            tracking_status = status_map.get(mal_tracking.get("status", 0), "Unknown")
        else:
            tracking_status = "Untracked"
            tracking_id = 0

        return MangaCard(
            title=title,
            tracking_status=tracking_status,
            mihon_status=mihon_status,
            chapter_text=chapter_text,
            is_nsfw=manga.get("isNsfw", False),
            categories=manga.get("categories", []),
            mal_id=tracking_id,
            tracker=self.tracker,
            thumbnail_url=thumbnail_url,
            url=manga.get("url", ""),
            show_thumbnail=self.show_thumbnails
        )

    def update_manga_list(self):
        """Update manga list based on current filters"""
        self.ids.manga_list.clear_widgets()
        self.manga_cards = []

        for manga in self.manga_entries.get('backupManga', []):
            card = self.create_manga_card(manga)
            self.manga_cards.append(card)
            if self.should_show_card(card):
                self.ids.manga_list.add_widget(card)

    def should_show_card(self, card):
        """Check if card should be shown based on current filters"""
        if card.is_nsfw and self.ids.nsfw_filter.active:
            return False

        selected_category = self.ids.category_filter.text
        if selected_category != self.categories['all']:
            category_id = next(k for k, v in self.categories.items() if v == selected_category)
            if category_id not in card.categories:
                return False

        return True

    def sort_manga_list(self, key, button):
        """Sort manga list by given key"""
        cards = list(self.ids.manga_list.children)

        self.sort_states[key] = not self.sort_states[key]
        reverse = self.sort_states[key]

        arrow = '▲' if reverse else '▼'
        button.text = f'Sort by {key.replace("_", " ").title()} {arrow}'

        if key == 'title':
            cards.sort(key=lambda x: x.title.lower(), reverse=reverse)
        elif key == 'tracking_status':
            cards.sort(key=lambda x: x.tracking_status, reverse=reverse)
        elif key == 'mihon_status':
            cards.sort(key=lambda x: x.mihon_status, reverse=reverse)

        self.ids.manga_list.clear_widgets()
        for card in reversed(cards):
            self.ids.manga_list.add_widget(card)

    def toggle_nsfw_filter(self, active):
        """Handle NSFW filter toggle"""
        self.update_manga_list()

    def on_category_selected(self, category):
        """Handle category selection"""
        self.update_manga_list()

    def get_read_chapters(self, manga):
        """Get number of read chapters"""
        return sum(1 for chapter in manga.get("chapters", []) if chapter.get("read", False))

    def update_json_data(self, mal_id, status, chapters, score):
        """Update manga data in JSON"""
        if not self.manga_entries:
            return

        print(f"Updating JSON data for MAL ID: {mal_id}, Status: {status}, Chapters: {chapters}, Score: {score}")

        for manga in self.manga_entries.get('backupManga', []):
            tracking = manga.get('tracking', [])
            mal_tracking = next((t for t in tracking if t.get('syncId') == 1), None)

            if mal_tracking and int(mal_tracking.get('mediaId', 0)) == int(mal_id):
                mal_tracking.update({
                    'status': self._convert_status_to_mal(status),
                    'lastChapterRead': int(chapters) if chapters else 0,
                    'score': int(score) if score != 'Score' else 0
                })
                self.save_manga_entries()
                return True
            elif not mal_tracking and manga.get('title') == self.selected_manga_title:
                new_tracking = {
                    'syncId': 1,
                    'mediaId': int(mal_id),
                    'status': self._convert_status_to_mal(status),
                    'lastChapterRead': int(chapters) if chapters else 0,
                    'score': int(score) if score != 'Score' else 0
                }
                manga['tracking'] = tracking + [new_tracking]
                self.save_manga_entries()
                return True
            elif not mal_tracking and manga.get('url') == self.selected_manga_url:
                new_tracking = {
                    'syncId': 1,
                    'mediaId': int(mal_id),
                    'status': self._convert_status_to_mal(status),
                    'lastChapterRead': int(chapters) if chapters else 0,
                    'score': int(score) if score != 'Score' else 0
                }
                manga['tracking'] = tracking + [new_tracking]
                self.save_manga_entries()
                return True
        return False

    def _convert_status_to_mal(self, status):
        """Convert status to MAL format"""
        status_map = {
            'Reading': 1,
            'Completed': 2,
            'On Hold': 3,
            'Dropped': 4,
            'Plan to Read': 6
        }
        return status_map.get(status, 6)

    def save_manga_entries(self):
        """Save manga entries to file"""
        if hasattr(self, 'last_loaded_file') and self.manga_entries:
            try:
                with open(self.last_loaded_file, 'w') as f:
                    json.dump(self.manga_entries, f, indent=2)
            except Exception as e:
                print(f"Failed to save JSON file: {str(e)}")

    def show_matching_popup(self):
        if self.tracker:
            popup = MangaMatchingPopup(self.tracker, self.manga_entries)
            popup.open()
        else:
            print("Please log in first")

    def toggle_thumbnails(self, *args):
        self.show_thumbnails = not self.show_thumbnails
        for card in self.manga_cards:
            card.show_thumbnail = self.show_thumbnails