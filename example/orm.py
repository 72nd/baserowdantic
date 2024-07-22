import random
from baserow.client import BatchResponse, GlobalClient
from baserow.field import CreatedByField, CreatedOnField, FileField, LastModifiedByField, LastModifiedOnField, MultipleCollaboratorsField, MultipleSelectField, SingleSelectField
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
BASEROW_URL = "https:/your.baserow.instance"
USER_EMAIL = "your-login-mail@example.com"
USER_PASSWORD = "your-secret-password"


def example_image() -> str:
    """Returns the path of the example image."""
    example_folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(example_folder, "example.png")


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

    name: Annotated[
        str,
        Field(alias=str("Name"), description="The name of the author"),
        PrimaryField(),
    ]
    """Defines the name field as the primary field in Baserow."""
    age: Optional[int] = Field(
        default=None, alias=str("Age"), description="The age of the author",
    )
    """
    Use the alias annotation if the field name in Baserow differs from the
    variable name. You can add a description which will be visible for the user
    on Baserow.
    """
    email: Optional[str] = Field(default=None, alias=str("E-Mail"))
    phone: Optional[str] = Field(default=None, alias=str("Phone"))


class Genre(str, enum.Enum):
    """Baserow has a single select field. This can be mapped to enums."""
    FICTION = "Fiction"
    EDUCATION = "Education"
    MYSTERY = "Mystery"


class Keyword(str, enum.Enum):
    """
    Baserow also has multiple select field. We use this book keywords as an
    example.
    """
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
        Field(description="What's this book about?", alias=str("Description")),
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
    GlobalClient.from_file(secrets_file)


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
    return ids


async def batch_populate_authors() -> list[int]:
    """
    When adding large amounts of data, it is recommended to use the batch
    functionality of the `BasicClient().create_rows()`. In this case, only one
    API call is made with all the newly added items.
    """
    new_rows: BatchResponse = await GlobalClient().create_rows(
        Author.table_id,
        [
            Author(
                name="Alice Johnson",
                age=37,
                email="alice.johnson@example.com",
                phone="+1 404 555 0193",
            ),
            Author(
                name="Bob Brown",
                age=35,
                email="bob.brown@example.com",
                phone="+1 505 555 0124",
            )
        ],
        True,
    )
    if hasattr(new_rows, "items"):
        return [new_row.row_id for new_row in new_rows.items]
    return []


async def populate_books(author_ids: list[int]) -> list[int]:
    """
    Populate the book table. Returns the ids of the new entries.
    """
    ids: list[int] = []
    # Add cover via local file path.
    new_row = await Book(
        title="The Great Adventure",
        description="A thrilling adventure story...",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.FICTION),
        keywords=MultipleSelectField.from_enums(
            Keyword.ADVENTURE, Keyword.FICTION),
        cover=await FileField.from_file(example_image()),
        published_date=datetime(2024, 7, 17),
        reading_duration=timedelta(hours=8),
        available=True,
        rating=4,
    ).create()
    ids.append(new_row.id)

    # Add cover from BufferedReader.
    image = open(example_image(), "rb")
    new_row = await Book(
        title="Cooking with Love",
        description="Delicious recipes to share with loved ones...",
        author=TableLinkField[Author].from_value(random.choice(author_ids)),
        genre=SingleSelectField.from_enum(Genre.EDUCATION),
        keywords=MultipleSelectField.from_enums(
            Keyword.EDUCATION, Keyword.TECH),
        cover=await FileField.from_file(image),
        published_date=datetime(2021, 2, 10),
        reading_duration=timedelta(hours=6),
        available=True,
        rating=5,
    ).create()
    ids.append(new_row.id)

    # Load cover from web URL.
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


async def update(author_ids: list[int], book_ids: list[int]):
    book_id = book_ids[0]

    # Update by ID
    await Book.update_fields_by_id(book_id, title="Gardening Basics")
    print(f"Set title of book id={book_id} to 'Gardening Basics'")

    # Update model instance: Manipulate by field name
    book = await Book.by_id(book_id)
    await book.update_fields(description="A beginner's guide to gardening.")
    print(f"Set description of book id={book_id} to 'A beginner's guide to gardening.'")  # noqa

    # Update model instance: Update instance to Baserow
    book.published_date = datetime(2021, 3, 5)
    book.reading_duration = timedelta(hours=6)
    book.rating = 5
    await book.update()

    # Manipulate select fields.
    if book.genre is not None:
        # Set a new value for the single select field.
        book.genre.set(Genre.EDUCATION)
    if book.keywords is not None:
        # Remove all current keywords.
        book.keywords.clear()
        # Add some new keywords.
        book.keywords.append(
            Keyword.EDUCATION, Keyword.BEGINNER, Keyword.MYSTERY, Keyword.FICTION,
        )
        # Remove keyword(s).
        book.keywords.remove(Keyword.MYSTERY, Keyword.FICTION)
    await book.update()

    # Modify link field.
    if book.author is not None:
        # Remove all current linked entries.
        book.author.clear()
        # Append author entry by row id and instance.
        author = await Author.by_id(author_ids[0])
        book.author.append(author_ids[1], author)
        await book.update()

    # Modify file field.
    if book.cover is not None:
        # Remove current file. And add two new ones.
        book.cover.clear()
        await book.cover.append_file(example_image())
        await book.cover.append_file_from_url("https://picsum.photos/180/320")
        await book.update()


async def delete():
    # Add some test entries.
    author1 = await Author(name="Test 1", age=23).create()
    author2 = await Author(name="Test 2", age=42).create()

    # Delete by id
    await Author.delete_by_id(author1.id)

    # Delete by instance
    author = await Author.by_id(author2.id)
    await author.delete()


async def run():
    config_client()
    await create_tables()
    author_ids = await populate_authors()
    author_ids.extend(await batch_populate_authors())
    book_ids = await populate_books(author_ids)
    await query(author_ids, book_ids)
    await update(author_ids, book_ids)
    await delete()


asyncio.run(run())
