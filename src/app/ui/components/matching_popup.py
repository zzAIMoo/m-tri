from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle
from kivy.app import App
from concurrent.futures import ThreadPoolExecutor
import asyncio
from difflib import SequenceMatcher
from typing import Dict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from core.trackers.base import BaseTracker

BATCH_SIZE = 1
WORKER_COUNT = 1
SCHEDULE_INTERVAL = 2

class MatchSearchPopup(Popup):
    def __init__(self, title, tracker, on_select, highlight_node=None, **kwargs):
        self.highlight_node = highlight_node
        super().__init__(**kwargs)
        self.title = f'Results for "{title}"'
        self.size_hint = (0.8, 0.8)
        self.tracker = tracker
        self.on_select = on_select

        self.content = self.build_content()
        self.search_mal(title)

    def build_content(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        scroll = ScrollView()
        self.results_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.results_list.bind(minimum_height=self.results_list.setter('height'))

        self.loading_label = Label(
            text='Searching...',
            size_hint_y=None,
            height=40
        )
        self.results_list.add_widget(self.loading_label)

        scroll.add_widget(self.results_list)
        content.add_widget(scroll)
        return content

    def search_mal(self, title):
        try:
            results = self.tracker.search_manga(title)
            self.results_list.clear_widgets()

            if not results or 'data' not in results or not results['data']:
                self.results_list.add_widget(Label(
                    text='No results found',
                    size_hint_y=None,
                    height=40
                ))
                return

            for manga in results['data']:
                node = manga['node']
                is_highlighted = (self.highlight_node and
                                self.highlight_node.get('id') == node.get('id'))

                result_btn = Button(
                    text=node['title'],
                    size_hint_y=None,
                    height=50,
                    background_normal='',
                    background_color=(0.6, 0.2, 0.8, 1) if is_highlighted else (0.2, 0.2, 0.2, 1),
                    halign='left'
                )
                if is_highlighted:
                    result_btn.text = f"✓ {node['title']} (Fuzzy Matched)"

                result_btn.bind(on_release=lambda btn, n=node: self.select_result(n))
                self.results_list.add_widget(result_btn)

        except Exception as e:
            self.results_list.clear_widgets()
            self.results_list.add_widget(Label(
                text=f'Search failed: {str(e)}',
                size_hint_y=None,
                height=40
            ))

    def select_result(self, node):
        self.on_select(node)
        self.dismiss()

class ClickableMangaItem(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if not self.matched:
                Color(0.3, 0.1, 0.1, 1)
            else:
                Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.pos, size=self.size)

class MangaMatchItem(ClickableMangaItem):
    STATUS_COLORS = {
        'pending': (0.7, 0.7, 0.7, 1),
        'in_progress': (1, 0.76, 0.03, 1),
        'matched': (0.2, 0.8, 0.2, 1),
        'fuzzy_matched': (0.6, 0.2, 0.8, 1),
        'no_match': (0.8, 0.2, 0.2, 1),
        'error': (0.8, 0.2, 0.2, 1)
    }

    title = StringProperty('')
    selected = BooleanProperty(False)
    matched = BooleanProperty(False)

    def __init__(self, title, main_popup, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.main_popup = main_popup
        self.orientation = 'horizontal'
        self.size_hint_y=None
        self.height = 40
        self.spacing = 10
        self.padding = [10, 5]

        self.checkbox = CheckBox(active=self.selected, size_hint_x=None, width=30)
        self.checkbox.bind(active=self.on_checkbox)

        self.add_widget(self.checkbox)
        title_label = Label(
            text=self.title,
            shorten=True,
            shorten_from='right',
            size_hint_x=0.8,
            halign='left',
            valign='middle'
        )
        title_label.bind(width=lambda *x: setattr(title_label, 'text_size', (title_label.width, None)))
        self.add_widget(title_label)

        self.status_label = Label(
            text='Pending',
            size_hint_x=None,
            width=100,
            color=self.STATUS_COLORS['pending']
        )
        self.add_widget(self.status_label)

        self._trigger_update = Clock.create_trigger(self.update_canvas)
        self.bind(pos=self._trigger_update, size=self._trigger_update)

        self.fuzzy_match_info = None

    def on_checkbox(self, instance, value):
        self.selected = value

    def set_status(self, status, text=None):
        if text is None:
            text = status.replace('_', ' ').title()
        self.status_label.text = text
        self.status_label.color = self.STATUS_COLORS.get(status, self.STATUS_COLORS['pending'])

    def set_match_status(self, matched):
        self.matched = matched
        if matched:
            self.set_status('matched', 'Matched')
        else:
            self.set_status('no_match', 'No Match')
        self.update_canvas()

    def on_release(self):
        if self.fuzzy_match_info:
            popup = MatchSearchPopup(
                title=self.title,
                tracker=self.main_popup.tracker,
                on_select=self.on_result_selected,
                highlight_node=self.fuzzy_match_info
            )
        else:
            popup = MatchSearchPopup(
                title=self.title,
                tracker=self.main_popup.tracker,
                on_select=self.on_result_selected
            )
        popup.open()

    def on_result_selected(self, node):
        try:
            self.mal_id = node['id']
            self.fuzzy_match_info = None
            self.set_status('matched', 'Matched')
            self.matched = True
            self.checkbox.active = True
        except Exception as e:
            print(f"Error selecting result: {e}")
            self.set_status('error', 'Error')

class MangaMatchingPopup(Popup):
    def __init__(self, tracker, manga_entries, **kwargs):
        super().__init__(**kwargs)
        self.tracker = tracker
        self.manga_entries = manga_entries
        self.title = 'Manga Matching'
        self.size_hint = (0.9, 0.9)
        self.manga_items = []
        self.current_match_index = 0
        self.executor = ThreadPoolExecutor(max_workers=WORKER_COUNT)

        self.content = self.build_content()

    def build_content(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        buttons_box = BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=10
        )

        match_btn = Button(
            text='Auto Match',
            size_hint_x=0.5,
            background_normal='',
            background_color=(0.2, 0.6, 0.9, 1)
        )
        match_btn.bind(on_release=self.start_matching)

        track_btn = Button(
            text='Track Selected',
            size_hint_x=0.5,
            background_normal='',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        track_btn.bind(on_release=self.track_selected)

        buttons_box.add_widget(match_btn)
        buttons_box.add_widget(track_btn)
        content.add_widget(buttons_box)

        self.progress_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=50,
            spacing=5,
            padding=[0, 10],
            opacity=0
        )

        self.progress_label = Label(
            text='Matching 0/0',
            size_hint_y=None,
            height=20
        )

        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=20
        )

        self.progress_box.add_widget(self.progress_label)
        self.progress_box.add_widget(self.progress_bar)
        content.add_widget(self.progress_box)

        scroll = ScrollView()
        self.manga_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5
        )
        self.manga_list.bind(minimum_height=self.manga_list.setter('height'))

        for manga in self.manga_entries.get('backupManga', []):
            if not any(t.get('syncId') == 1 for t in manga.get('tracking', [])):
                item = MangaMatchItem(
                    title=manga.get('title', 'Unknown'),
                    main_popup=self
                )
                self.manga_items.append(item)
                self.manga_list.add_widget(item)

        scroll.add_widget(self.manga_list)
        content.add_widget(scroll)

        return content

    async def match_manga_parallel(self, manga_items):
        tasks = []
        for item in manga_items:
            task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.tracker.search_manga,
                item.title
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    def match_manga_batch(self, dt):
        batch_size = BATCH_SIZE
        end_index = min(self.current_match_index + batch_size, len(self.manga_items))
        batch_items = self.manga_items[self.current_match_index:end_index]

        futures = []
        for manga_item in batch_items:
            manga_item.set_status('in_progress', 'Searching...')
            future = self.executor.submit(self.process_single_manga, manga_item)
            futures.append(future)

        for future in futures:
            future.result()

        progress = (end_index) / len(self.manga_items) * 100
        self.progress_bar.value = progress
        self.progress_label.text = f'Matching {end_index}/{len(self.manga_items)}'

        self.current_match_index = end_index
        if self.current_match_index >= len(self.manga_items):
            self.progress_box.opacity = 0
            return False
        return True

    def process_single_manga(self, manga_item):
        """Process a single manga item in a separate thread"""
        try:
            results = self.tracker.search_manga(manga_item.title, limit=5)
            if results and 'data' in results and results['data']:
                best_match = None
                highest_ratio = 0

                for result in results['data']:
                    node = result['node']
                    title = node['title']
                    alt_titles = []

                    if 'alternative_titles' in node:
                        alt_titles.extend(node['alternative_titles'].get('synonyms', []))
                        if node['alternative_titles'].get('en'):
                            alt_titles.append(node['alternative_titles']['en'])
                        if node['alternative_titles'].get('ja'):
                            alt_titles.append(node['alternative_titles']['ja'])

                    ratio = fuzz.ratio(manga_item.title.lower(), title.lower())
                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match = node

                    for alt_title in alt_titles:
                        ratio = fuzz.ratio(manga_item.title.lower(), alt_title.lower())
                        if ratio > highest_ratio:
                            highest_ratio = ratio
                            best_match = node

                if highest_ratio == 100:
                    matched = True
                    is_fuzzy = False
                elif highest_ratio >= 85:
                    matched = True
                    is_fuzzy = True
                else:
                    matched = False
                    is_fuzzy = False

                if is_fuzzy:
                    manga_item.fuzzy_match_info = best_match

                Clock.schedule_once(lambda dt: self.update_manga_status(
                    manga_item, matched, best_match['id'] if matched else None, is_fuzzy
                ))
            else:
                Clock.schedule_once(lambda dt: manga_item.set_match_status(False))
        except Exception as e:
            print(f"Error matching {manga_item.title}: {e}")
            Clock.schedule_once(lambda dt: manga_item.set_status('error', 'Error'))

    def update_manga_status(self, manga_item, matched, mal_id=None, is_fuzzy=False):
        """Update manga item status on the main thread"""
        if matched:
            status = 'fuzzy_matched' if is_fuzzy else 'matched'
            manga_item.set_status(status, 'Fuzzy Match' if is_fuzzy else 'Matched')
        else:
            manga_item.set_status('no_match', 'No Match')

        manga_item.matched = matched
        manga_item.checkbox.active = matched
        if matched:
            manga_item.mal_id = mal_id

    def start_matching(self, *args):
        self.current_match_index = 0
        self.progress_box.opacity = 1
        self.progress_bar.value = 0
        self.progress_label.text = f'Matching 0/{len(self.manga_items)}'

        for item in self.manga_items:
            item.set_status('pending')

        Clock.schedule_interval(self.match_manga_batch, SCHEDULE_INTERVAL)

    def track_selected(self, *args):
        selected_items = [item for item in self.manga_items if item.selected and hasattr(item, 'mal_id')]
        if not selected_items:
            return

        self.progress_box.opacity = 1
        self.progress_bar.value = 0
        self.progress_label.text = f'Tracking 0/{len(selected_items)}'

        batch_size = 10
        current_index = 0

        def process_tracking_batch(dt):
            nonlocal current_index

            end_index = min(current_index + batch_size, len(selected_items))
            batch_items = selected_items[current_index:end_index]

            futures = []
            for item in batch_items:
                future = self.executor.submit(self.track_single_manga, item)
                futures.append(future)

            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in tracking batch: {e}")

            progress = (end_index) / len(selected_items) * 100
            self.progress_bar.value = progress
            self.progress_label.text = f'Tracking {end_index}/{len(selected_items)}'

            current_index = end_index
            if current_index >= len(selected_items):
                app = App.get_running_app()
                app.root.save_manga_entries()
                self.progress_box.opacity = 0
                self.dismiss()
                return False
            return True

        Clock.schedule_interval(process_tracking_batch, 0.8)

    def track_single_manga(self, item):
        """Track a single manga item in a separate thread"""
        try:
            self.tracker.add_manga(item.mal_id)

            for manga in self.manga_entries.get('backupManga', []):
                if manga.get('title') == item.title:
                    if 'tracking' not in manga:
                        manga['tracking'] = []
                    manga['tracking'].append({
                        'syncId': 1,
                        'mediaId': item.mal_id,
                        'status': 6,
                        'score': 0,
                        'lastChapterRead': 0
                    })
                    break

            Clock.schedule_once(lambda dt: item.set_status('matched', 'Tracked'))

        except Exception as e:
            print(f"Error tracking {item.title}: {e}")
            Clock.schedule_once(lambda dt: item.set_status('error', 'Track Error'))

    def fuzzy_match_titles(self, title1, title2):
        """Compare titles using various fuzzy matching techniques"""
        clean1 = clean_title(title1)
        clean2 = clean_title(title2)

        ratio = fuzz.ratio(clean1, clean2)
        partial_ratio = fuzz.partial_ratio(clean1, clean2)
        token_sort_ratio = fuzz.token_sort_ratio(clean1, clean2)
        token_set_ratio = fuzz.token_set_ratio(clean1, clean2)

        return max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)

def titles_match(title1, title2, threshold=0.85):
    clean_title1 = clean_title(title1)
    clean_title2 = clean_title(title2)

    if clean_title1.lower() == clean_title2.lower():
        return True

    ratio = SequenceMatcher(None, clean_title1.lower(), clean_title2.lower()).ratio()
    return ratio >= threshold

def clean_title(title):
    """Clean title for better matching"""
    import re

    clean = title.lower()

    common_words = ['the', 'a', 'an', 'to', 'no', 'wa', 'ga', 'wo', 'de', 'ni']
    clean = re.sub(r'[^\w\s]', ' ', clean)

    words = clean.split()
    words = [w for w in words if w not in common_words]

    clean = ' '.join(words)
    clean = re.sub(r'season \d+', '', clean)
    clean = re.sub(r'part \d+', '', clean)
    clean = re.sub(r'\s+', ' ', clean)

    return clean.strip()