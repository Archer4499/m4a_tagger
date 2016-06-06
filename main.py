import queue
import threading
from glob import glob
from os import chdir
from tkinter import *
from tkinter import ttk, filedialog, messagebox

from mutagen.mp4 import MP4, MP4StreamInfoError

from utils import get_external_tags

__author__ = 'Derek'


TAGS = [["Title:\t", "\xa9nam"], ["Album:\t", "\xa9alb"], ["Artist:\t", "\xa9ART"],
        ["Track:\t", "trkn"], ["Year:\t", "\xa9day"], ["Genre:\t", "\xa9gen"]]
OTHER_TAGS = {"aART": "Album artist:", "\xa9wrt": "Composer:", "\xa9cmt": "Comment:",
              "desc": "Description:", "purd": "Purchase date:", "\xa9grp": "Grouping:",
              "\xa9lyr": "Lyrics:", "purl": "Podcast URL:", "egid": "Podcast episode GUID:",
              "catg": "Podcast category:", "keyw": "Podcast keywords:",
              "\xa9too": "Encoded by:", "cprt": "Copyright:", "soal": "Album sort order:",
              "soaa": "Album artist sort order:", "soar": "Artist sort order:",
              "sonm": "Title sort order:", "soco": "Composer sort order:",
              "sosn": "Show sort order:", "tvsh": "Show name:", "cpil": "Compilation:",
              "pgap": "Gapless album:", "pcst": "Podcast:", "disk": "Disc number, total:",
              "tmpo": "Tempo/BPM, 16 bit int:"}
with open("genres.txt", "r") as f:
    GENRES = f.read().splitlines()


class Settings(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.transient(parent)
        self.title("Settings")
        self.parent = parent
        self.result = None

        body = ttk.Frame(self)
        body.pack(padx=5, pady=5)

        self.browser = IntVar()
        self.browser.set(int(parent.browser))
        c = ttk.Checkbutton(body, text="Open in browser", variable=self.browser)
        c.grid(column=0, row=0, sticky=W)
        c.focus_set()

        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))

        self.wait_window(self)

    def buttonbox(self):
        box = ttk.Frame(self)

        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def cancel(self, *_):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    def apply(self):
        self.parent.browser = bool(self.browser.get())

    def ok(self, *_):
        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()


class CurrentInfo:
    class CurrentEntry(ttk.Entry):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.state(["readonly"])

    def __init__(self, parent, column):
        self.var_list = [StringVar() if i is not 3 else [StringVar(), StringVar()] for i in range(len(TAGS))]

        ttk.Label(parent, text="Current:").grid(column=column, row=0, sticky=W)

        title = self.CurrentEntry(parent, textvariable=self.var_list[0])
        title.grid(column=column, row=1, sticky=(W, E))

        album = self.CurrentEntry(parent, textvariable=self.var_list[1])
        album.grid(column=column, row=2, sticky=(W, E))

        artist = self.CurrentEntry(parent, textvariable=self.var_list[2])
        artist.grid(column=column, row=3, sticky=(W, E))

        # Track
        track_frame = ttk.Frame(parent, padding=(5, 0))
        track_frame.grid(column=column, row=4, sticky=W)
        track = self.CurrentEntry(track_frame, width=3, textvariable=self.var_list[3][0])
        track.grid(column=0, row=0, sticky=(W, E))
        # /
        ttk.Label(track_frame, text="/").grid(column=1, row=0)
        # Total Tracks
        track_total = self.CurrentEntry(track_frame, width=3, textvariable=self.var_list[3][1])
        track_total.grid(column=2, row=0, sticky=(W, E))

        year = self.CurrentEntry(parent, width=5, textvariable=self.var_list[4])
        year.grid(column=column, row=5, sticky=W)

        genre = self.CurrentEntry(parent, textvariable=self.var_list[5])
        genre.grid(column=column, row=6, sticky=(W, E))


class NewEntry:
    class NumEntry(ttk.Entry):
        def __init__(self, length, min_val, max_val, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.length = length
            self.min_val = min_val
            self.max_val = max_val
            self.configure(width=self.length + 1, validate="key",
                           validatecommand=(self.register(self.on_validate), "%P"))

        def on_validate(self, new_value):
            if new_value.strip() == "":
                return True
            try:
                value = int(new_value)
                if value < self.min_val or value > self.max_val or len(str(value)) > self.length:
                    raise ValueError
            except ValueError:
                self.bell()
                return False
            return True

    def __init__(self, parent, column, select_var, name):
        self.var_list = [StringVar() if i is not 3 else [StringVar(), StringVar()] for i in range(len(TAGS))]

        ttk.Label(parent, text=name).grid(column=column, row=0, sticky=W)

        self.title = ttk.Entry(parent, textvariable=self.var_list[0])
        self.title.grid(column=column, row=1, sticky=(W, E))

        album = ttk.Entry(parent, textvariable=self.var_list[1])
        album.grid(column=column, row=2, sticky=(W, E))

        artist = ttk.Entry(parent, textvariable=self.var_list[2])
        artist.grid(column=column, row=3, sticky=(W, E))

        #  Track
        track_frame = ttk.Frame(parent, padding=(5, 0))
        track_frame.grid(column=column, row=4, sticky=W)
        track = self.NumEntry(2, 0, 99, track_frame, textvariable=self.var_list[3][0])
        track.grid(column=0, row=0, sticky=(W, E))
        # /
        ttk.Label(track_frame, text="/").grid(column=1, row=0)
        # Total Tracks
        track_total = self.NumEntry(2, 0, 99, track_frame, textvariable=self.var_list[3][1])
        track_total.grid(column=2, row=0, sticky=(W, E))

        year = self.NumEntry(4, 0, 9999, parent, textvariable=self.var_list[4])
        year.grid(column=column, row=5, sticky=W)

        genre = ttk.Combobox(parent, textvariable=self.var_list[5], values=GENRES)
        genre.grid(column=column, row=6, sticky=(W, E))

        select = ttk.Radiobutton(parent, variable=select_var, value=name)
        select.grid(column=column, row=7)


class MenuBar(Menu):
    def __init__(self, root, close):
        super().__init__()

        self.option_add("*tearOff", FALSE)

        file_menu = Menu(self)
        file_menu.add_command(label="Settings",
                              command=lambda: Settings(root))
        file_menu.add_command(label="Exit", command=close)

        help_menu = Menu(self)
        help_menu.add_command(label="About",
                              command=lambda: messagebox.showinfo("About", "This is an Mp4 tagger"))

        self.add_cascade(menu=file_menu, label="File")
        self.add_cascade(menu=help_menu, label="Help")

        root.config(menu=self)


class Gui(Tk):
    def __init__(self):
        super().__init__()

        self.title("M4a Tagger")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        MenuBar(self, self.quit)

        self.songs = []
        self.total_songs = 0
        self.current_song = MP4()
        self.current_song_file_name = StringVar("")
        self.extra_tags = dict()
        self.browser = True

        mainframe = ttk.Frame(self, padding=(3, 3, 0, 0))
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        # Clears focus from text boxes on click
        mainframe.bind("<1>", lambda event: mainframe.focus_set())

        self.entry_select = StringVar(value="Dbpedia:")
        self.init_columns(mainframe)

        self.extra_tags_var = StringVar()
        self.init_extra(mainframe, 9)

        self.custom_url = StringVar()
        self.init_custom_url(mainframe, 8)

        self.progress = StringVar(value="Song 0 of 0")
        self.init_buttons(mainframe)

        # Add padding to most widgets
        for child in mainframe.winfo_children():
            if type(child) != ttk.Frame:
                child.grid_configure(padx=5, pady=5)

        ttk.Sizegrip(self).grid(column=999, row=999, sticky=(S, E))

        self.load_queue = queue.Queue()

    def init_columns(self, mainframe):
        # Row Labels
        for i, item in enumerate(TAGS):
            ttk.Label(mainframe, text=item[0]).grid(column=0, row=i + 1, sticky=E)

        self.current_info = CurrentInfo(mainframe, 1)
        mainframe.columnconfigure(1, weight=1, uniform="a")

        self.dbpedia_entry = NewEntry(mainframe, 2, self.entry_select, "Dbpedia:")
        self.dbpedia_entry.title.focus()
        mainframe.columnconfigure(2, weight=1, uniform="a")

        self.wiki_entry = NewEntry(mainframe, 3, self.entry_select, "Wikipedia:")
        mainframe.columnconfigure(3, weight=1, uniform="a")

        self.discogs_entry = NewEntry(mainframe, 4, self.entry_select, "Discogs:")
        mainframe.columnconfigure(4, weight=1, uniform="a")

        ttk.Label(mainframe, text="Select tag source:").grid(column=1, row=7, sticky=W)
        ttk.Label(mainframe, textvariable=self.current_song_file_name)\
            .grid(column=1, columnspan=2, row=8, sticky=W)

    def init_extra(self, mainframe, row_num):
        ttk.Label(mainframe, text="The following tags will be removed:") \
            .grid(column=1, columnspan=2, row=row_num, sticky=W)

        extra_tags_frame = ttk.Frame(mainframe, padding=(5, 0), borderwidth=2, relief="sunken")
        extra_tags_frame.grid(column=1, columnspan=2, row=row_num+1, sticky=(W, E), padx=5)

        ttk.Label(extra_tags_frame, textvariable=self.extra_tags_var, font="TkFixedFont") \
            .grid(column=0, row=0, sticky=(W, E))

    def init_custom_url(self, mainframe, row_num):
        ttk.Label(mainframe, text="Enter wikipedia url if the sources are incorrect:") \
            .grid(column=3, columnspan=2, row=row_num, sticky=W)

        custom_url_frame = ttk.Frame(mainframe)
        custom_url_frame.grid(column=3, columnspan=2, row=row_num+1, sticky=(W, E), padx=(5, 0))

        ttk.Label(custom_url_frame, text="en.wikipedia.org/wiki/") \
            .grid(column=0, row=0, sticky=W)

        custom_url_entry = ttk.Entry(custom_url_frame, textvariable=self.custom_url)
        custom_url_entry.grid(column=1, row=0, sticky=W)

        self.custom_url_button = ttk.Button(custom_url_frame, text="Load Info", command=self.load_url)
        self.custom_url_button.grid(column=2, row=0)
        self.custom_url_button.state(["disabled"])

    def init_buttons(self, mainframe):
        button_frame = ttk.Frame(mainframe, padding=(5, 10, 0, 0))
        button_frame.grid(column=2, columnspan=3, row=100, sticky=E)

        self.progress_bar = ttk.Progressbar(button_frame, orient="horizontal", length=50, mode="indeterminate")
        self.progress_bar.grid(column=0, row=0)
        self.progress_bar.grid_remove()

        ttk.Label(button_frame, textvariable=self.progress).grid(column=1, row=0)

        self.save_button = ttk.Button(button_frame, text="Save", command=self.save)
        self.save_button.grid(column=2, row=0)
        self.save_button.state(["disabled"])

        self.next_song_button = ttk.Button(button_frame, text="Next Song", command=self.next_song)
        self.next_song_button.grid(column=3, row=0)
        self.next_song_button.state(["disabled"])

        self.browse_button = ttk.Button(button_frame, text="Open Folder", command=self.browse)
        self.browse_button.grid(column=4, row=0)

    @staticmethod
    def set_var_list(var_list, tag_list):
        for i, var in enumerate(var_list):
            if i is 3:
                var[0].set(tag_list[i][0])
                if tag_list[i][1]:
                    var[1].set(tag_list[i][1])
                else:
                    var[1].set("")
            else:
                var.set(tag_list[i])

    def threaded_set_external_tags(self, title, wiki_path, browser):
        self.load_queue.put(get_external_tags(title=title, wiki_page=wiki_path, browser=browser))

    def process_load_queue(self):
        try:
            external_tags = self.load_queue.get_nowait()
        except queue.Empty:
            self.after(100, self.process_load_queue)
        else:
            self.set_var_list(self.dbpedia_entry.var_list, external_tags[0])
            self.set_var_list(self.wiki_entry.var_list, external_tags[1])
            self.set_var_list(self.discogs_entry.var_list, external_tags[2])
            self.progress_bar.stop()
            self.progress_bar.grid_remove()

    def set_external_tags(self, title="", wiki_path="", browser=None):
        # TODO: auto load next song
        self.progress_bar.grid()
        self.progress_bar.start()

        if browser is None:
            browser = self.browser
        if wiki_path:
            wiki_path = "http://en.wikipedia.org/wiki/" + wiki_path

        # Downloads tags from Dbpedia, Wikipedia and Discogs (takes 11 seconds on average)
        threading.Thread(target=self.threaded_set_external_tags, args=(title, wiki_path, browser)).start()

        self.process_load_queue()

    def set_vars(self, external=True):
        def tag_name_value(tag_key):
            tag = self.extra_tags[tag_key]
            if type(tag) is list:
                value = tag[0]
            else:
                value = tag

            return OTHER_TAGS.get(tag_key, tag_key).ljust(24) + str(value)

        def get_extra_tags():
            if "covr" in self.extra_tags:
                del self.extra_tags["covr"]
            if self.extra_tags:
                return "\n".join([tag_name_value(tag_key) for tag_key in self.extra_tags])
            else:
                return "None"

        self.custom_url.set("")

        self.extra_tags = dict(self.current_song.tags)
        song_tags = [self.extra_tags.pop(tag[1], "None")[0] for tag in TAGS]

        self.set_var_list(self.current_info.var_list, song_tags)

        self.extra_tags_var.set(get_extra_tags())

        self.progress.set(value="Song "+str(self.total_songs-len(self.songs))+" of "+str(self.total_songs))

        if external:
            self.set_external_tags(title=song_tags[0])

    def load_url(self):
        # Bound to custom_url_button
        url = self.custom_url.get()
        if url:
            self.set_external_tags(wiki_path=url, browser=False)

    def open_next_song(self):
        while self.songs:
            try:
                self.current_song_file_name.set(self.songs.pop())
                self.current_song = MP4(self.current_song_file_name.get())
            except MP4StreamInfoError as e:
                print(repr(e))
            else:
                return True
        return False

    def browse(self):
        # Bound to browse_button
        directory = filedialog.askdirectory(parent=self, mustexist=True)
        if not directory:
            return
        try:
            chdir(directory)
        except OSError as e:
            messagebox.showerror(title="Error", message=repr(e))
            return

        self.songs = glob("*.m4a")
        if not self.songs:
            messagebox.showerror(title="Error", message="No .m4a files in the given directory")
            return
        self.songs.sort()
        self.songs.reverse()
        self.total_songs = len(self.songs)

        if not self.open_next_song():
            messagebox.showerror(title="Error", message="No valid .m4a files in the given directory")
            return

        self.set_vars()

        self.custom_url_button.state(["!disabled"])
        self.save_button.state(["!disabled"])
        self.save_button.config(text="Save")
        if self.songs:
            self.next_song_button.state(["!disabled"])

    def save(self):
        # Bound to save_button
        if self.extra_tags:
            for tag in self.extra_tags:
                del self.current_song[tag]

        if self.entry_select.get() == "Dbpedia:":
            var_save = self.dbpedia_entry.var_list
        elif self.entry_select.get() == "Wikipedia:":
            var_save = self.wiki_entry.var_list
        else:
            var_save = self.discogs_entry.var_list

        for i, var in enumerate(var_save):
            if i is 3:
                self.current_song[TAGS[i][1]] = [(int("0" + var[0].get()), int("0" + var[1].get()))]
            else:
                self.current_song[TAGS[i][1]] = [var.get()]

        try:
            self.current_song.save()
        except Exception as e:
            messagebox.showerror(title="Error", message="Couldn't save tags to file",
                                 detail=repr(e))
        else:
            self.set_vars(False)
            self.save_button.state(["disabled"])
            self.save_button.config(text="Saved")

    def next_song(self):
        # Bound to next_song_button
        if not self.open_next_song():
            messagebox.showerror(title="Error", message="No more valid .m4a files in directory")
            self.next_song_button.state(["disabled"])
            return

        if not self.songs:
            self.next_song_button.state(["disabled"])
        self.save_button.state(["!disabled"])
        self.save_button.config(text="Save")

        self.set_vars()


if __name__ == '__main__':
    Gui().mainloop()
