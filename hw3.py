from collections import UserDict
from datetime import datetime, timedelta
import re
import os
import platform
import pickle


def clear_console():

    system = platform.system()

    if system == "Windows":
        os.system('cls')
    else:
        os.system('clear')


class PhoneFormatError(Exception):

    def __init__(self):
        super().__init__('''Phone number must have 10 numbers and 
must contain just numbers!''')


class BirthdayFormatError(Exception):

    def __init__(self):
        super().__init__('''Birthday format is must be DD.MM.YYYY!''')


class Field:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Name(Field):
    pass


class Phone(Field):

    def __init__(self, value):
        if not self.validate_phone(value):
            raise PhoneFormatError()
        super().__init__(value)

    def validate_phone(self, value):
        return value.isdigit() and len(value) == 10


class Birthday(Field):

    def __init__(self, value):
        self.validate_birthday(value)

        day, month, year = value.split('.')
        super().__init__(datetime(int(year), int(month), int(day)))

    def validate_birthday(self, value):
        pattern = r"\d{2}\.\d{2}\.\d{4}"

        if not re.match(pattern, value):
            raise BirthdayFormatError()


class Record:

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        # self.birthday = None

    def add_birthday(self, value):
        self.birthday = Birthday(value)

    def show_birthday(self):
        if self.birthday is not None:
            return self.birthday.value.strftime('%d-%m-%Y')
        else:
            return 'Birthday info not found.'

    def add_phone(self, phone):
        phone = Phone(phone)
        for p in self.phones:
            if p.value == phone.value:
                return 'You already have this phone number.'
        self.phones.append(phone)
        return 'Phone number added.'

    def remove_phone(self, phone):
        phone = Phone(phone)
        for p in self.phones:
            if p.value == phone.value:
                self.phones.remove(phone)
                return 'Phone number removed.'
        return 'Phone number not found.'

    def edit_phone(self, phone1, phone2):
        for p in self.phones:
            if p.value == phone1:
                p.value = phone2
                return 'Phone number added.'
        return 'Phone number not found.'

    def find_phone(self, phone):
        phone = Phone(phone)
        for p in self.phones:
            if p.value == phone.value:
                return p.value
        return 'Phone number not found.'

    def __str__(self):
        return f'''Contact name: {self.name.value}, phones: {'; '.join([p.value for p in self.phones])}'''


class AddressBook(UserDict):

    def __init__(self):
        self.filename = 'data'
        super().__init__()
        if os.path.exists('data'):
            self.load_records()
        else:
            self.data = {}

    def add_record(self, record: Record):
        if record.name.value not in self.data:
            self.data[record.name.value] = record
            return 'New contact with number added.'
        else:
            contact: Record = self.find(record.name.value)
            contact.add_phone(record.phones[0].value)
            return 'Phone number added.'

    def save_records(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.data, f)

    def load_records(self):
        if (os.path.getsize(self.filename) > 0):
            with open(self.filename, 'rb') as f:
                self.data = pickle.load(f)
        else:
            self.data = {}

    def find(self, name: Name):
        return self.data[name]

    def delete(self, name: Name):
        del self.data[name]

    def get_birthdays_per_week(self):
        now = datetime.now().date()
        delta_next_week = 7 - now.weekday()
        next_week_start = now + timedelta(days=delta_next_week)
        next_week_end = next_week_start + timedelta(days=6)

        birthdays = {}

        current_date = next_week_start

        while (current_date <= next_week_end):
            birthdays[current_date.strftime('%A')] = []
            current_date += timedelta(days=1)

        for user in self.data:
            if hasattr(self.data[user], 'birthday'):
                if self.data[user].birthday is not None:
                    birthday = datetime(
                        now.year, self.data[user].birthday.value.month, self.data[user].birthday.value.day).date()
                    if next_week_start <= birthday <= next_week_end:
                        birthdays[birthday.strftime('%A')].append(
                            self.data[user].name.value)
        return "\n".join([f'{k}: {", ".join(v)}' for k, v in birthdays.items() if len(v) > 0])


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and phone please."
        except KeyError:
            return "Contact not found!"
        except IndexError:
            return "Give me name please."
    return inner


@input_error
def add_contact(args, contacts: AddressBook):
    try:
        name, phone = args
        contact = Record(name)
        contact.add_phone(phone)
        result = contacts.add_record(contact)
        contacts.save_records()
        return result
    except PhoneFormatError as e:
        return e


@input_error
def change_contact(args, contacts: AddressBook):
    try:
        name, phone1, phone2 = args
        contact = contacts.find(name)
        for phone in contact.phones:
            phone1 = Phone(phone1)
            if phone1.value == phone.value:
                phone.value = phone2
                contacts.save_records()
                return "Phone number updated."
            return "Phone number not found."
    except PhoneFormatError as e:
        return e


@input_error
def show_phone(args, contacts: AddressBook):
    contact = contacts.find(args[0])
    return f'{contact.name.value}: { ", ".join([phone.value for phone in contact.phones])}'


def show_all(contacts: AddressBook):
    return '\n'.join([f'{k} ({v.birthday.value.strftime("%d.%m.%Y") if hasattr(v,"birthday") else "No Birthday"}): { ", ".join([phone.value for phone in v.phones])}' for k, v in contacts.items()])


def add_birthday(args, contacts: AddressBook):
    try:
        name, birthday = args
        contact = contacts.find(name)
        contact.add_birthday(birthday)
        contacts.save_records()
        return 'Birthday added.'
    except BirthdayFormatError as e:
        return e
    except ValueError:
        return 'You need to give name and birthday #dd.mm.yyyy'


def show_birthday(args, contacts: AddressBook):
    name = args[0]
    contact = contacts.find(name)
    return contact.show_birthday()


def birthdays(contacts: AddressBook):
    return contacts.get_birthdays_per_week()


def parseCommands(input):
    if input == '':
        return '', []

    cmd, *args = input.strip().lower().split()
    return cmd, args


def main():
    print('Welcome to the Contact Assistant!')

    contacts = AddressBook()

    while (True):
        cmd, args = parseCommands(input('> '))
        clear_console()
        if cmd == 'hello':
            print('How can I help you?')
        elif (cmd == 'close' or cmd == 'exit'):
            print('Good bye!')
            break
        elif cmd == 'phone':
            print(show_phone(args, contacts))
        elif cmd == 'add':
            print(add_contact(args, contacts))
        elif cmd == 'change':
            print(change_contact(args, contacts))
        elif cmd == 'all':
            print(show_all(contacts))
        elif cmd == 'add-birthday':
            print(add_birthday(args, contacts))
        elif cmd == 'show-birthday':
            print(show_birthday(args, contacts))
        elif cmd == 'birthdays':
            print(birthdays(contacts))
        else:
            print('Invalid command.')


if __name__ == '__main__':
    main()
