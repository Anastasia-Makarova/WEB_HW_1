import re
import pickle
from pathlib import Path
from collections import UserList


class Note:
    def __init__(self, title: str, text: str) -> None:
        self.__title = title
        self.__text = text
        self.__tags_dict = {}
        self.__parse_tags()

    def __str__(self) -> str:
        tags = ', '.join(tag for tag in self.__tags_dict.keys())
        return "{:<30} {:<50} {:<50}".format(self.title, tags, self.text)

    @property
    def title(self) -> str:
        return self.__title
    
    @title.setter
    def title(self, value: str) -> None:
        self.__title = value

    @property
    def text(self)  -> str:
        return self.__text
    
    @text.setter
    def text(self, value: str) -> None:
        self.__text = value
        self.__parse_tags()

    @property
    def tags_dict(self) -> dict:
        return self.__tags_dict

    def __parse_tags(self) -> None:
        pattern = r"#\w+"
        tags = re.findall(pattern, self.__text)
    
        for tag in tags:
            tag = tag[1:]
            self.__tags_dict[tag] = self.__tags_dict.get(tag, 0) + 1


class NotesList(UserList):
    def __init__(self, root_path: Path) -> None:
        super().__init__()
        self.filename = str(root_path.joinpath("notes.bin"))
        self.load_notes_from_file()

    def append(self, note) -> None:
        super().append(note)
        self._save_notes_to_file()

    def remove(self, param: str) -> None:
        index = None
        if param.isdigit():
            index = int(param) - 1            
        else:
            for i, note in enumerate(self.data):
                if note.title.lower() == param.lower():
                    index = i
                    break
        if index is not None:                  
            del self.data[index]
            self._save_notes_to_file()
            return True
        return False

    def edit(self, param: str, title:str, text:str) -> bool:
        index = None
        if param.isdigit():
            index = int(param) -1            
        else:
            for i, note in enumerate(self.data):
                if note.title.lower() == param.lower():
                    index = i
                    break
        if index is not None:                     
            note = Note(title, text)
            self.data[index] = note
            self._save_notes_to_file()
            return True
        return False

    def _save_notes_to_file(self) -> None:
        with open(self.filename, 'wb') as file:
            pickle.dump(self.data, file)

    def load_notes_from_file(self) -> None:
        try:
            with open(self.filename, 'rb') as file:
                self.data = pickle.load(file)
        except (FileNotFoundError, EOFError):
            self.data = []
    
    def output_notes(self) -> list:
        output = []
        output.append("{:<5} {:<30} {:<50} {:<50}".format("num", "title", "tags", "text"))
        output += list(map(lambda note: f"{(self.data.index(note)+1):<5} {str(note)}" , self.data))
        return output

    def search(self, query) -> list:
        matches = []
        for note in self.data:
            if query.lower() in note.text.lower() or query.lower() in note.title.lower():
                matches.append(note)
        return matches
    
    def sort_by_tag_count(self) -> list:
        sorted_notes = sorted(self.data, key=lambda note: sum(note.tags_dict.values()), reverse=True)
        return sorted_notes
    
    def search_by_tag(self, tag: str) -> list:
        notes = [note for note in self.data if tag in note.tags_dict]
        return sorted(notes, key=lambda note: note.tags_dict[tag], reverse=True)