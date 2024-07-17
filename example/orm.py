import random
from baserow.client import GlobalClient
from baserow.field import CreatedByField, CreatedOnField, FileField, LastModifiedByField, LastModifiedOnField, MultipleCollaboratorsField, MultipleSelectField, SelectEntry, SingleSelectField
from baserow.field_config import Config, LongTextFieldConfig, PrimaryField, RatingFieldConfig, RatingStyle
from baserow.filter import AndFilter
from baserow.table import Table, TableLinkField
from pydantic import UUID4, Field, ConfigDict
from typing_extensions import Annotated

import asyncio
from datetime import datetime, timedelta
import enum
import json
import os
from typing import Optional


# ADAPT THIS CONSTANTS TO YOUR ENVIRONMENT. Or add a `secrets.json` in the
# examples folder.
BASEROW_URL = "https://your.baserow.instance"
USER_EMAIL = "your-login-mail@example.com"
USER_PASSWORD = "your-secret-password"


class Author(Table):
    """
    First, let's define the Authors table. Note the two class variables: table_id
    and table_name.
    """

    table_id = 1420
    """
    This class variable defines the ID of the table in Baserow. It can be
    omitted if the table has not been created yet.
    """
    table_name = "Author"
    """Name of the Table in Baserow."""
    model_config = ConfigDict(populate_by_name=True)
    """This model_config is necessary, otherwise it won't work."""

    name: Annotated[str, Field(alias=str("Name")), PrimaryField()]
    """Defines the name field as the primary field in Baserow."""
    age: int = Field(alias=str("Age"))
    """
    Use the alias annotation if the field name in Baserow differs from the
    variable name.
    """
    email: Optional[str] = Field(default=None, alias=str("E-Mail"))
    phone: Optional[str] = Field(default=None, alias=str("Phone"))


class Genre(str, enum.Enum):
    """Baserow has a single select field. This can be mapped to enums."""
    FICTION = "Fiction"
    EDUCATION = "Education"
    MYSTERY = "Mystery"


class Keyword(str, enum.Enum):
    ADVENTURE = "Adventure"
    FICTION = "Fiction"
    SQL = "SQL"
    EDUCATION = "Education"
    TECH = "Tech"
    MYSTERY = "Mystery"
    THRILLER = "Thriller"
    BEGINNER = "Beginner"


class Book(Table):
    table_id = 1421
    table_name = "Book"
    model_config = ConfigDict(populate_by_name=True)

    title: Annotated[str, Field(alias=str("Title")), PrimaryField()]
    """Title serves as the primary field."""
    description: Annotated[
        Optional[str],
        Config(LongTextFieldConfig()),
        Field(alias=str("CV")),
    ]
    """
    Since a long text field is also just a string, this configuration must be
    specified through a Config object.
    """
    author: Optional[TableLinkField[Author]] = Field(
        default=None,
        alias=str("Author"),
    )
    """Link to the Author table."""
    genre: Optional[SingleSelectField[Genre]] = Field(
        default=None,
        alias=str("Genre"),
    )
    """A single select based on the Genre enum."""
    keywords: Annotated[
        Optional[MultipleSelectField[Keyword]],
        Field(
            alias=str("Keywords"),
            default=None,
        ),
    ]
    """A multiple select based on the Keyword enum."""
    cover: Optional[FileField] = Field(
        default=None,
        alias=str("Cover"),
    )
    """Save files using the file field."""
    published_date: Optional[datetime] = Field(
        default=None, alias=str("Published Date"))
    reading_duration: Optional[timedelta] = Field(
        default=None, alias=str("Reading Duration"))
    available: bool = Field(alias=str("Available"))
    """Checkbox."""
    rating: Annotated[
        int,
        Config(RatingFieldConfig(max_value=5, style=RatingStyle.HEART)),
        Field(alias=str("Rating")),
    ]
    uuid: Optional[UUID4] = Field(default=None, alias=str("UUID"))
    created_on: Optional[CreatedOnField] = Field(
        default=None, alias=str("Created on"))
    created_by: Optional[CreatedByField] = Field(
        default=None, alias=str("Created by"))
    last_modified: Optional[LastModifiedOnField] = Field(
        default=None, alias=str("Last modified"),
    )
    last_modified_by: Optional[LastModifiedByField] = Field(
        default=None, alias=str("Last modified by"),
    )
    collaborators: Optional[MultipleCollaboratorsField] = Field(
        default=None, alias=str("Collaborators"))


def config_client():
    example_folder = os.path.dirname(os.path.abspath(__file__))
    secrets_file = os.path.join(example_folder, "secrets.json")
    if not os.path.exists(secrets_file):
        GlobalClient.configure(
            BASEROW_URL,
            email=USER_EMAIL,
            password=USER_PASSWORD,
        )
        return
    with open(secrets_file, "r") as f:
        data = json.load(f)
    GlobalClient.configure(
        data["url"],
        email=data["email"],
        password=data["password"],
    )


async def create_tables():
    """
    If the table does not yet exist in Baserow, it can be created. For this, the
    ID of the database where the table should be created must be provided.
    """
    await Author.create_table(227)
    await Book.create_table(227)


async def populate_authors() -> list[int]:
    """
    Populate the author table. Returns the ids of the new entries.
    """
    ids: list[int] = []
    new_row = await Author(
        name="John Doe",
        age=23,
        email="john.doe@example.com",
        phone="+1 891 796 3774",
    ).create()
    ids.append(new_row.id)

    new_row = await Author(
        name="Jane Smith",
        age=30,
        email="jane.smith@example.com",
        phone="+1 303 555 0142",
    ).create()
    ids.append(new_row.id)

    new_row = await Author(
        name="Alice Johnson",
        age=37,
        email="alice.johnson@example.com",
        phone="+1 404 555 0193",
    ).create()
    ids.append(new_row.id)

    new_row = await Author(
        name="Bob Brown",
        age=35,
        email="bob.brown@example.com",
        phone="+1 505 555 0124",
    ).create()
    ids.append(new_row.id)
    return ids


async def populate_books(author_ids: list[int]) -> list[int]:
    """
    Populate the book table. Returns the ids of the new entries.
    """
    ids: list[int] = []
    new_row = await Book(
        title="The Great Adventure",
        description="A thrilling adventure story...",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.FICTION),
        keywords=MultipleSelectField.from_enums(
            Keyword.ADVENTURE, Keyword.FICTION),
        cover=await FileField.from_url("https://picsum.photos/180/320"),
        published_date=datetime(2024, 7, 17),
        reading_duration=timedelta(hours=8),
        available=True,
        rating=4,
    ).create()
    ids.append(new_row.id)

    new_row = await Book(
        title="Cooking with Love",
        description="Delicious recipes to share with loved ones...",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.EDUCATION),
        keywords=MultipleSelectField.from_enums(
            Keyword.EDUCATION, Keyword.TECH),
        cover=await FileField.from_url("https://picsum.photos/180/320"),
        published_date=datetime(2021, 2, 10),
        reading_duration=timedelta(hours=6),
        available=True,
        rating=5,
    ).create()
    ids.append(new_row.id)

    new_row = await Book(
        title="Mystery of the Night",
        description="A mystery novel set in the dark...",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.MYSTERY),
        keywords=MultipleSelectField.from_enums(
            Keyword.MYSTERY, Keyword.THRILLER),
        cover=await FileField.from_url("https://picsum.photos/180/320"),
        published_date=datetime(2020, 11, 10),
        reading_duration=timedelta(hours=10),
        available=False,
        rating=3,
    ).create()
    ids.append(new_row.id)

    new_row = await Book(
        title="The History of Space Exploration",
        description="A comprehensive history of space missions.",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.EDUCATION),
        keywords=MultipleSelectField.from_enums(
            Keyword.EDUCATION, Keyword.TECH),
        cover=await FileField.from_url("https://picsum.photos/180/320"),
        published_date=datetime(2022, 1, 15),
        reading_duration=timedelta(hours=14),
        available=True,
        rating=5,
    ).create()
    ids.append(new_row.id)

    new_row = await Book(
        title="Romantic Escapades",
        description="Stories of love and romance...",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.FICTION),
        keywords=MultipleSelectField.from_enums(
            Keyword.FICTION, Keyword.ADVENTURE),
        cover=await FileField.from_url("https://picsum.photos/180/320"),
        published_date=datetime(2023, 6, 18),
        reading_duration=timedelta(hours=9),
        available=True,
        rating=4,
    ).create()
    ids.append(new_row.id)
    return ids


async def query(author_ids: list[int], book_ids: list[int]):
    """
    This method showcases how to access individual entries using the internal
    unique row ID and filter queries. Additionally, it demonstrates the neatly
    formatted output of the records.
    """
    # By ID.
    random_author = await Author.by_id(random.choice(author_ids))
    print(f"Author entry with id={random_author.row_id}: {random_author}")

    random_book = await Book.by_id(random.choice(book_ids))
    print(f"Book entry with id={random_book.row_id}: {random_book}")

    # All authors between the ages of 30 and 40, sorted by age.
    filtered_authors = await Author.query(
        filter=AndFilter().higher_than_or_equal("Age", "30").lower_than_or_equal("Age", "40"),  # noqa
        order_by=["Age"],
    )
    print(f"All authors between 30 and 40: {filtered_authors}")

    # All entries of the Books table. Handles paginated results from Baserow,
    # making multiple API calls if necessary. Use with caution, as it can cause
    # server load with very large tables. The page size is set to 100 by default
    # and can be increased to a maximum of 200. Setting the size to -1 only
    # makes sense if there are more than 200 entries in the table.
    all_books = await Author.query(size=-1)
    print(f"All books: {all_books}")

    # For linked entries, initially only the key value and the row_id of the
    # linked records are available. Using `TableLinkField.query_linked_rows()`,
    # the complete entries of all linked records can be retrieved.
    if random_book.author is not None:
        authors = await random_book.author.query_linked_rows()
        print(f"Author(s) of book {random_book.title}: {authors}")

    # Because the query has already been performed once, the cached result is
    # immediately available.
    if random_book.author is not None:
        print(await random_book.author.cached_query_linked_rows())

    # To access stored files, you can use the download URL. Please note that for
    # security reasons, this link has a limited validity.
    if random_book.cover is not None:
        for file in random_book.cover.root:
            print(f"Download the book cover: {file.url}")


async def run():
    config_client()
    # await create_tables()
    # author_ids = await populate_authors()
    # book_ids = await populate_books(author_ids)
    # await query(author_ids, book_ids)
    await query([4], [5])  # TEST

    # UPDATE ENTRY
    # TODO Text
    # book_entry = await Book.by_id(8)
    # with open("misc/town.png", "rb") as f:
    #     await book_entry.cover.append_file(f)
    # await book_entry.cover.append_file_from_url("https://picsum.photos/id/14/400/300")
    # await book_entry.update()
    # if book_entry.author is not None:
    #     book_entry.author.append(6)
    #     await book_entry.update()
    # if book_entry.genre is not None:
    #     book_entry.genre.set(Genre.EDUCATION)
    #     await book_entry.update()
    # print(book_entry)


asyncio.run(run())
