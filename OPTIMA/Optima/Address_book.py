import re
import pickle
from pathlib import Path
from datetime import date, timedelta
from functools import reduce
from collections import UserDict


class DuplicatedPhoneError(Exception):
    ...

class Field():
    def __init__(self, value: str):
        self.__value = value

    def __str__(self) -> str:
        return str(self.__value)
    
    def _set_value(self, value: str):
        self.__value = value

    @property
    def value(self) -> str:
        return self.__value


class Name(Field):
    ...


class Address(Field):
    ...


class Email(Field):
    def __init__(self, value: str) -> None:
        self.value = value
    
    @property
    def value(self) -> str:
        return super().value

    @value.setter
    def value(self, value: str):
        super()._set_value(self.__validate(value))

    def __validate(self, value: str) -> str:
        pattern = r'[a-zA-Z][a-zA-Z0-9_.]+@[a-z]+\.[a-z]{2,}'
        if re.match(pattern, value):
            return value
        else:
            raise ValueError(f"Email '{value}' is invalid. Check and try again")


class Phone(Field):
    def __init__(self, value: str) -> None:
        self.value = value
    
    @property
    def value(self) -> str:
        return super().value

    @value.setter
    def value(self, value: str):
        super()._set_value(self.__validate(value))

    def __validate(self, value: str) -> str:
        value = reduce((lambda a, b: a.replace(b, "")), "+()-", value)        
        if value.isdigit() and len(value) == 10:
            return value
        else:
            raise ValueError(f"Phone number'{value}' is incorrect. Phone number should consist of 10 digits.")


class Birthday(Field):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def value(self):
        return super().value

    @property
    def date(self):
        return date(self.__year, self.__month, self.__day)

    @property
    def day(self):
        return self.__day

    @property
    def month(self):
        return self.__month

    @property
    def year(self):
        return self.__year

    @value.setter
    def value(self, value: str):
        self.__year, self.__month, self.__day = self.__validate(value)
        super()._set_value(f"{self.__day}-{self.__month}-{self.__year}")

    def __validate(self, value: str) -> tuple:
        separator = "." if "." in value else "/" if "/" in value else "-"
        date_parts = value.split(separator)
        if len(date_parts) == 3:
            day, month, year = date_parts[:]
            if day.isdigit() and month.isdigit() and year.isdigit():
                if date(int(year), int(month), int(day)):
                    return int(year), int(month), int(day)
        raise ValueError(f"Birthday '{value}' format is incorrect. Use DD-MM-YYYY format")


class Record:
    def __init__(self, name: str, phone=None, birthday=None, address=None, email=None):
        self.name = Name(name)
        self.phones = [Phone(phone)] if phone else []
        self.birthday = Birthday(birthday) if birthday else "not set"
        self.address = Address(address) if address else "not set"
        self.email = Email(email) if email else "not set"

    def __str__(self):
        # return f"Contact name: {self.name}, phones: {'; '.join(p.value for p in self.phones)}, email: {self.email}, birthday: {self.birthday}, address: {self.address}"
        return "{:<10} {:<40} {:<35} {:<15} {:<60}".format(f"{self.name}", '; '.join(p.value for p in self.phones), f"{self.email}", f"{self.birthday}", f"{self.address}")
    

    def add_phone(self, phone: str): 
        existing_phone = self.find_phone(phone)
        if not existing_phone:
            self.phones.append(Phone(phone))
        else:
            raise DuplicatedPhoneError(self.name, phone)

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self) -> int:
        if isinstance(self.birthday, Birthday):
            next_birthday = self.birthday.date.replace(year=date.today().year)
            if next_birthday < date.today():
                next_birthday = next_birthday.replace(year=next_birthday.year+1)
            delta = next_birthday - date.today()
            return delta.days

    def edit_phone(self, old_phone: str, new_phone: str):
        existing_phone = self.find_phone(old_phone)
        if existing_phone:
            idx = self.phones.index(existing_phone)
            self.phones[idx] = Phone(new_phone)
        else:
            raise ValueError(f"Phone number {old_phone} not found for contact {self.name}.")
                
    def remove_phone(self, phone: str):
        existing_phone = self.find_phone(phone)
        if existing_phone:
            self.phones.remove(existing_phone)
        else:
            raise ValueError(f"Phone number {phone} not found for contact {self.name}.")
                            
    def find_phone(self, phone: str):
        existing_phone = list(filter(lambda p: p.value == phone, self.phones))
        if len(existing_phone) > 0:
            return existing_phone[0]
        
    def has_phone(self, term: str) -> bool:
        phones = list(filter(lambda p: term in p.value, self.phones))
        return len(phones) > 0
    
    def add_address(self, address: str):
        self.address = Address(address)

    def add_email(self, email: str):
        self.email = Email(email)
        

class AddressBook(UserDict):
    def __init__(self, file_name):
        self.__file_name = file_name
        super().__init__()
        
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str, suppress_error=False) -> Record:
        if name in self.data.keys():
            return self.data[name]
        if not suppress_error:
            raise KeyError

    def delete(self, name: str) -> Record:
        if name in self.data.keys():
            return self.data.pop(name)
    
    def __values(self) -> list:
        return list(self.data.values())
    
    def iterator(self, n=5):
        counter = 0
        values = self.__values()
        while counter < len(values):
            yield list(map(lambda record: str(record), values[counter: counter + n]))
            counter += n

    def __enter__(self):
        if Path(self.__file_name).exists():
            with open(self.__file_name, "rb") as fh:
                self.data = pickle.load(fh)
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> bool:
        with open(self.__file_name, "wb") as fh:
            pickle.dump(self.data, fh)
        if exception_type:
            return(f"There was an error during execution: {exception_type.__name__} = {exception_value}")
        return True
    
    def search_contacts(self, term) -> list:
        result = list(filter(lambda contact: term in contact.name.value.lower() or contact.has_phone(term), self.data.values()))
        return result

    def contacts_upcoming_birthdays(self, n=7) -> list:        
        contacts_with_birthdays = filter(lambda contact: isinstance(contact.birthday, Birthday), self.data.values())
        upcoming_birthdays = filter(lambda contact: contact.days_to_birthday() <= n, contacts_with_birthdays)
        return upcoming_birthdays