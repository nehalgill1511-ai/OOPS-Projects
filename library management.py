# ===== Complete Library Management System Project =====

# ---------- src/models.py ----------
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Set
from abc import ABC, abstractmethod
from datetime import date


class FinePolicy(ABC):
    @abstractmethod
    def calculate(self, days_late: int) -> float:
        pass


class SimpleFinePolicy(FinePolicy):
    def __init__(self, per_day: float = 5.0):
        self.per_day = per_day

    def calculate(self, days_late: int) -> float:
        return max(0, days_late) * self.per_day


@dataclass
class Book:
    book_id: str
    title: str
    author: str
    __available: bool = field(default=True, repr=False)

    def borrow(self) -> None:
        if not self.__available:
            raise ValueError("Book is not available")
        self.__available = False

    def return_book(self) -> None:
        self.__available = True

    def is_available(self) -> bool:
        return self.__available


@dataclass
class Member:
    member_id: str
    name: str
    __borrowed_books: Set[str] = field(default_factory=set, repr=False)

    def borrow_book(self, book_id: str, limit: int = 3) -> None:
        if len(self.__borrowed_books) >= limit:
            raise ValueError("Borrow limit reached")
        self.__borrowed_books.add(book_id)

    def return_book(self, book_id: str) -> None:
        if book_id not in self.__borrowed_books:
            raise ValueError("Book not borrowed by member")
        self.__borrowed_books.remove(book_id)

    @property
    def borrowed_books(self) -> Set[str]:
        return set(self.__borrowed_books)


@dataclass
class BorrowRecord:
    member_id: str
    book_id: str
    borrow_date: date
    return_date: Optional[date] = None


# ---------- src/library.py ----------
from typing import Dict, List
from datetime import date


class Library:
    def __init__(self, fine_policy: FinePolicy):
        self.fine_policy = fine_policy
        self.books: Dict[str, Book] = {}
        self.members: Dict[str, Member] = {}
        self.records: List[BorrowRecord] = []

    def add_book(self, book_id: str, title: str, author: str) -> None:
        if book_id in self.books:
            raise ValueError("Book ID already exists")
        self.books[book_id] = Book(book_id, title, author)

    def add_member(self, member_id: str, name: str) -> None:
        if member_id in self.members:
            raise ValueError("Member ID already exists")
        self.members[member_id] = Member(member_id, name)

    def borrow_book(self, member_id: str, book_id: str, borrow_date: date) -> None:
        if member_id not in self.members:
            raise ValueError("Invalid member")
        if book_id not in self.books:
            raise ValueError("Invalid book")

        book = self.books[book_id]
        member = self.members[member_id]

        book.borrow()
        member.borrow_book(book_id)

        self.records.append(BorrowRecord(member_id, book_id, borrow_date))

    def return_book(self, member_id: str, book_id: str, return_date: date) -> float:
        if member_id not in self.members:
            raise ValueError("Invalid member")
        if book_id not in self.books:
            raise ValueError("Invalid book")

        member = self.members[member_id]
        book = self.books[book_id]

        member.return_book(book_id)
        book.return_book()

        record = next(
            (r for r in self.records if r.member_id == member_id and r.book_id == book_id and r.return_date is None),
            None,
        )

        if not record:
            raise ValueError("No active borrow record")

        record.return_date = return_date

        allowed_days = 14
        days_late = max(0, (return_date - record.borrow_date).days - allowed_days)

        return self.fine_policy.calculate(days_late)


# ---------- cli.py ----------
from datetime import date


def run_cli():
    library = Library(SimpleFinePolicy())

    while True:
        print("\nLibrary Menu")
        print("1. Add Book")
        print("2. Add Member")
        print("3. Borrow Book")
        print("4. Return Book")
        print("5. Exit")

        choice = input("Choose option: ")

        try:
            if choice == "1":
                bid = input("Book ID: ")
                title = input("Title: ")
                author = input("Author: ")
                library.add_book(bid, title, author)
                print("Book added!")

            elif choice == "2":
                mid = input("Member ID: ")
                name = input("Name: ")
                library.add_member(mid, name)
                print("Member added!")

            elif choice == "3":
                mid = input("Member ID: ")
                bid = input("Book ID: ")
                library.borrow_book(mid, bid, date.today())
                print("Book borrowed!")

            elif choice == "4":
                mid = input("Member ID: ")
                bid = input("Book ID: ")
                fine = library.return_book(mid, bid, date.today())
                print(f"Book returned! Fine: {fine}")

            elif choice == "5":
                break

            else:
                print("Invalid choice")

        except Exception as e:
            print("Error:", e)


# ---------- tests/test_library.py ----------
import unittest


class TestLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = Library(SimpleFinePolicy(2))
        self.lib.add_book("b1", "Test Book", "Author")
        self.lib.add_member("m1", "Ali")

    def test_borrow_and_return(self):
        from datetime import timedelta

        borrow_date = date.today()
        self.lib.borrow_book("m1", "b1", borrow_date)

        return_date = borrow_date + timedelta(days=16)
        fine = self.lib.return_book("m1", "b1", return_date)

        self.assertEqual(fine, 4)  # 2 days late * 2 per day


if __name__ == "__main__":
    run_cli()
