<p align="right">
<picture>
  <source media="(prefers-color-scheme: dark)" width="160" srcset="misc/toc-indicator-dark.svg">
  <img alt="arrow pointing on the table of content button" width="160" src="misc/toc-indicator-light.svg">
</picture>
</p>
<p align="center">
  <img src="misc/logo.svg" alt="" width="350">
</p>
<p align="center">
  <a href="https://72nd.github.io/baserowdantic/baserow.html">📙 Documentation</a> – 
  <a href="https://github.com/72nd/baserowdantic/blob/main/example/orm.py">🚀 Comprehensive example</a>
</p>

# baserowdantic

**Caution:** This project is in active development and should currently be considered alpha. Therefore, bugs and (fundamental) breaking changes to the API can occur at any time.

This package provides a [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) (Create, Read, Update, Delete) client for [Baserow](https://baserow.io/), an open-source alternative to Airtable. Baserow offers a spreadsheet-like interface in the browser for accessing a relational database. Currently, there are numerous (partial) implementations of the Baserow API in Python. baserowdantic emerged from our specific needs and aims to achieve the following:

- Support CRUD operations on Baserow tables.
- Optionally abstract the operations to a [Pydantic](https://pydantic.dev/)-like model with all the benefits of Pydantic (validation, automatic (de-)serialization of data). This is what is understood as [ORM](https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping)-like.
- Be fully asynchronous.

As such, it is quite opinionated and supports only a small subset of the API. Users seeking more functionality may consider alternatives like the [python-baserow-client](https://github.com/NiklasRosenstein/python-baserow-client). Interaction with Baserow is facilitated through the definition of Pydantic models, ensuring data validation. The library is written to be fully asynchronous, integrating well with frameworks such as [FastAPI](https://fastapi.tiangolo.com/).

The package can be used in two different ways:

1. [Direct Editing with API Basic Client](#basic-client): You can directly edit with Baserow using the API Basic Client.
2. [Executing Actions on a Pydantic Model](#orm-like-access-using-models): Actions can be executed on a pydantic model. In this case, the table structure only needs to be defined once, and the library uses this information for all actions such as creating tables, reading and writing entries, and more.

## Walkthrough / Introductory Example

This sections offers a hands-on look at the ORM capabilities of baserowdantic. **Not in the mood for lengthy explanations?** Then check out the [examples/orm.py](https://github.com/72nd/baserowdantic/blob/main/example/orm.py) example directly. It demonstrates how to work with all the implemented field types.

This introduction provides only a brief overview of the functions. For a more detailed description of all features, please refer to the sections below.

### Client

For more information please refer to [the documentation below](#obtaining-a-client).

The connection to Baserow is managed through a client object. For this simple example, we will define a global client singleton which is used by default in all methods. Authentication is possible with a token or with login credentials. Creating tables requires login with credentials.

```python
GlobalClient.configure(
    "https://your.baserow.instance",
    email="your-login-mail@example.com",
    password="your-secret-password",
)
```

### Defining the Models

First, we need to define the structure of the two tables (authors and books) in a [`Table`](https://72nd.github.io/baserowdantic/baserow/table.html#Table) model. Please note the class variables [`table_id`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.table_id) and [`table_name`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.table_name). These link the model to the corresponding table in Baserow.

```python
from baserow.client import GlobalClient
from baserow.field import FileField, SelectEntry, SingleSelectField
from baserow.field_config import PrimaryField
from baserow.table import Table, TableLinkField
from pydantic import Field, ConfigDict
from typing_extensions import Annotated

class Author(Table):
    # This class variable defines the ID of the table in Baserow. It can be
    # omitted if the table has not been created yet.
    table_id = 23
    # Name of the Table in Baserow.
    table_name = "Author"
    # This model_config is necessary, otherwise it won't work.
    model_config = ConfigDict(populate_by_name=True)

    # Defines the name field as the primary field in Baserow
    name: Annotated[str, Field(alias=str("Name")), PrimaryField()]
    # Use the alias annotation if the field name in Baserow differs from the
    # variable name.
    age: Optional[int] = Field(
      default=None,
      alias=str("Age"),
      description="This field description will be visible for Baserow users",
    )


# Select fields are represented as enums. Therefore we define one for the genres.
class Genre(str, enum.Enum):
    FICTION = "Fiction"
    EDUCATION = "Education"
    MYSTERY = "Mystery"


# The Book model demonstrates some more advanced field types.
class Book(Table):
    table_id = 42
    table_name = "Book"
    model_config = ConfigDict(populate_by_name=True)

    title: Annotated[str, Field(alias=str("Title")), PrimaryField()]
    # Link to the Author.
    author: Optional[TableLinkField[Author]] = Field(
        default=None,
        alias=str("Author"),
    )
    # A single select field.
    genre: Optional[SingleSelectField[Genre]] = Field(
        default=None,
        alias=str("Genre"),
    )
    # Store files like a cover image.
    cover: Optional[FileField] = Field(
        default=None,
        alias=str("Cover"),
    )
```

### Create tables

With the model defining the table structure, baserowdantic's [`Table.create_table()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.create_table) can create the tables based on it. This step requires authentication using login credentials (JWT Tokens, more info [here](#authentication)). The `table_id` ClassVar does not need to be set in the model when initially creating the table in Baserow. However, it must be set afterward to allow further modifications to the table.

The method requires the database ID where the table should be created. You can find this ID in the Baserow user interface.

```python
await Author.create_table(227)
await Book.create_table(227)
```


### Creating entries

Now that the tables are set up in the database, you can start populating them with entries using [`Table.create()](https://72nd.github.io/baserowdantic/baserow/table.html#Table.create). The following example provides insights into the various methods available.

```python
# Let's start by creating a few authors.
john = await Author(name="John Doe", age=23).create()
jane = await Author(name="Jane Smith", age=42).create()
anna = await Author(name="Anna Thompson", age=36).create()

# Let's continue with the books. Note how we link the newly created authors to
# the books and also add covers from both a local file and a URL.
first_book = await Book(
  title="The Great Adventure",
  genre=SingleSelectField.from_enum(Genre.FICTION),
  author=TableLinkField[Author].from_value(john.id),
  cover=await FileField.from_file(open("path/to/cover.png", "rb")),
).create()
second_book = await Book(
  title="Mystery of the Night",
  genre=SingleSelectField.from_enum(Genre.MYSTERY),
  author=TableLinkField[Author].from_value(jane.id),
  cover=await FileField.from_url("https://picsum.photos/id/14/400/300")
).create()
```

Please note that [`Table.create()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.create) only returns a [`MinimalRow`](https://72nd.github.io/baserowdantic/baserow/client.html#MinimalRow), which contains only the entry's `id`. The complete dataset must be retrieved using a [`Table.by_id()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.by_id) query.

```python
complete_first_book_entry = await Book.by_id(first_book.id)
```

Head now to your baserow installation. You'll find two new tables »Author« and »Book«. Which look something like this:

![The book table in Baserow](misc/book-table.png)
When adding large amounts of data, it is recommended to use the batch functionality of the BasicClient(). In this case, only one API call is made with all the newly added items. See this example in [examples/orm.py](https://github.com/72nd/baserowdantic/blob/main/example/orm.py).


### Querying Data

Now that records are present in the table, you can start querying them. Besides a simple query by unique ID using [`Table.by_id()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.by_id), you can also formulate complex query filters (based on a [`AndFilter`](https://72nd.github.io/baserowdantic/baserow/filter.html#AndFilter) or [`OrFilter`](https://72nd.github.io/baserowdantic/baserow/filter.html#OrFilter)). Additionally, you can set the sorting, result page size, and the number of results. If you want to fetch all entries, you can set the `size` parameter to `-1`.

```python
# Getting the entry by its unique ID.
complete_jane_record = Author.by_id(jane.id)
print(complete_jane_record)

# An example of a more complex query: All authors between the ages of 30 and 40,
# sorted by age.
filtered_authors = await Author.query(
    filter=AndFilter().higher_than_or_equal("Age", "30").lower_than_or_equal("Age", "40"),
    order_by=["Age"],
)
print(filtered_authors)
```

The results from Baserow are paginated (default is 100 per request, maximum can be set to 200 using the `size` parameter). If desired, the library can automatically handle querying larger tables through multiple requests by setting `size` to -1. Use this option with caution, as it can create server load for large tables.

```python
all_books = await Author.query(size=-1)
print(f"All books: {all_books}")
```

Let's now take a look at Linked Fields. For linked entries, initially only the key value and the row_id of the linked records are available. Using [`TableLinkField.query_linked_rows()`](https://72nd.github.io/baserowdantic/baserow/table.html#TableLinkField.query_linked_rows), the complete entries of all linked records can be retrieved. When dealing with complex database structures where many rows have multiple linked entries, this can lead to significant wait times due to repeated queries. To address this, there is an option to cache the results. If [`TableLinkField.cached_query_linked_rows()`](https://72nd.github.io/baserowdantic/baserow/table.html#TableLinkField.cached_query_linked_rows) is used, the dataset is queried only the first time.

```python
book = Book.by_id(BOOK_ID)
authors = await book.author.query_linked_rows()
print(f"Author(s) of book {book.title}: {authors}")

# Because the query has already been performed once, the cached result is
# immediately available.
print(await book.author.cached_query_linked_rows())
```

To access stored files, you can use the download URL. Please note that for security reasons, this links have a limited validity.

```python
for file in random_book.cover.root:
  print(f"Download the book cover: {file.url}")
```

### Update records

This section demonstrates how to modify existing entries in Baserow. The approach differs between basic types and advanced types like files or select fields. Let's start by looking at the basic types.

There are three distinct methods to update entries. [`Table.update_fields_by_id()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.update_fields_by_id) is used when the ID of the row to be modified is known, but the full dataset is not yet available on the client. The fields to be updated are specified as keyword arguments.

Similarly, [`Table.update_fields`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.update_fields) uses keyword arguments but requires the complete instance to be available. Multiple fields can be updated by their names and corresponding values.

Lastly, you can modify the local instance and then use [`Table.update()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.update) to apply all changes to Baserow. This method is the only approach for advanced types. You have to remember to call the `update()` method. Otherwise your changes will be lost. The program will warn you, when a instance with unwritten changes was deleted by the garbage collector.

```python
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
```

Manipulate single and multiple select fields. Again: Don't forget to update.

```python
# Set a new value for the single select field.
book.genre.set(Genre.EDUCATION)

# Remove all current keywords.
book.keywords.clear()
# Add some new keywords.
book.keywords.append(
    Keyword.EDUCATION, Keyword.BEGINNER, Keyword.MYSTERY, Keyword.FICTION,
)
# Remove keyword(s).
book.keywords.remove(Keyword.MYSTERY, Keyword.FICTION)
await book.update()
```

Modify link fields. Works almost As multiple select fields.

```python
# Remove all current linked entries.
book.author.clear()

# Append author entry by row id and instance.
author = await Author.by_id(author_ids[0])
book.author.append(author_ids[1], author)
await book.update()
```

Modify file fields. As always: Don't forget to update in the end.

```python
# Remove current file. And add two new ones.
book.cover.clear()
await book.cover.append_file(example_image())
await book.cover.append_file_from_url("https://picsum.photos/180/320")
await book.update()
```

### Delete records

There are two ways: Delete by `row_id` using [`Table.delete_by_id()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.delete_by_id) or call [`Table.delete()`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.delete) on a instance.

```python
# Delete by id
await Author.delete_by_id(ROW_ID)

# Delete by instance
author = await Author.by_id(ROW_ID)
await author.delete()
```


## Obtaining a Client

The [`Client`](https://72nd.github.io/baserowdantic/baserow/client.html#Client) manages the actual HTTP calls to the Baserow REST API. It can be used directly or, ideally, through the model abstraction provided by Pydantic, which is the primary purpose of this package.

### Authentication

Access to the Baserow API requires authentication, and there are [two methods available](https://baserow.io/docs/apis/rest-api) for this:

- **Database Tokens:** These tokens are designed for delivering data to frontends and, as such, can only perform CRUD (Create, Read, Update, Delete) operations on a database. New tokens can be created in the User Settings, where their permissions can also be configured. For instance, it is possible to create a token that only allows reading. These tokens have unlimited validity.
- **JWT Tokens:** All other functionalities require a JWT token, which can be obtained by providing login credentials (email address and password) to the Baserow API. These tokens have a limited lifespan of 10 minutes and will be refreshed if needed.

The client in this package can handle both types of tokens. During initialization, you can provide either a Database Token or the email address and password of a user account. For most use cases, the Database Token is sufficient and recommended.

The following example demonstrates how to instantiate the client using either of the available authentication methods. Please note that only one of these methods should be used at a time.

```python
from baserow import Client

# With a database token.
client = Client("baserow.example.com", token="<API-TOKEN>")

# With user email and password.
client = Client("baserow.example.com", email="baserow.user@example.com", password="<PASSWORD>")

# Usage example.
table_id = 23
total_count = await client.table_row_count(table_id)
```

### Add a client to a Table

If a specific client is required for a table, it can be added as follows.

```python
client = Client("baserow.example.com", token="<API-TOKEN>")

class Author(Table):
  table_id = 23
  table_name = "Author"
  model_config = ConfigDict(populate_by_name=True)
  client = client
```

### Singleton/Global Client

In many applications, maintaining a consistent connection to a single Baserow instance throughout the runtime is crucial. To facilitate this, the package provides a [Global Client](https://72nd.github.io/baserowdantic/baserow/client.html#GlobalClient), which acts as a singleton. This means the client needs to be configured just once using GlobalClient.configure(). After this initial setup, the Global Client can be universally accessed and used throughout the program.

When utilizing the ORM functionality of the table models, all methods within the table models inherently use this Global Client. Please note that the Global Client **can only be configured once**. Attempting to call the [`GlobalClient.configure()`](https://72nd.github.io/baserowdantic/baserow/client.html#GlobalClient.configure) method more than once will result in an exception. 

```python
from baserow import GlobalClient

# Either configure the global client with a database token...
GlobalClient.configure("baserow.example.com", token="<API-TOKEN>")

# ...or with the login credentials (email and password).
GlobalClient.configure(
    "baserow.example.com",
    email="baserow.user@example.com",
    password="<PASSWORD>",
)

# Use the global client just like you would use any other client instance.
persons = await GlobalClient().get_row(23, 42, True, Person)
```

This setup ensures that your application maintains optimal performance by reusing the same client instance, minimizing the overhead associated with establishing multiple connections or instances.

## Basic Client

Even though Baserowdantic focuses on interacting with Pydantic using Pydantic data models, the Client class used can also be directly employed. The [Client class](https://72nd.github.io/baserowdantic/baserow/client.html#Client) provides CRUD (create, read, update, delete) operations on a Baserow table. It is entirely asynchronous.


### Count Table Rows

[This method](https://72nd.github.io/baserowdantic/baserow/client.html#Client.table_row_count) returns the number of rows or records in a Baserow table. Filters can be optionally passed as parameters.

```python
from baserow import Client, AndFilter

client = Client("baserow.example.com", token="<API-TOKEN>")

table_id = 23
total_count = await client.table_row_count(table_id)
dave_count = await client.table_row_count(
    table_id,
    filter=AndFilter().contains("Name", "Dave"),
)
print(f"Total persons: {total_count}, persons called Dave: {dave_count}")

client.close()
```

### List Table Fields

[This function](https://72nd.github.io/baserowdantic/baserow/client.html#Client.list_fields) retrieves the fields (also known as rows) present in a specified table along with their configurations. The return value contains the information in the form of the `FieldConfig` model.

```python
table_id = 23
print(await client.list_fields(table_id))
```


### List Table Rows

[The method](https://72nd.github.io/baserowdantic/baserow/client.html#Client.list_table_rows) reads the entries or records of a table in Baserow. It is possible to filter, sort, select one of the pages (Baserow API uses paging), and determine the number (size) of returned records (between 1 to 200). If it is necessary to retrieve all entries of a table, the method [`Client().list_all_table_rows`](https://72nd.github.io/baserowdantic/baserow/client.html#Client.list_table_rows) exists for this purpose. This method should be used with caution, as many API calls to Baserow may be triggered depending on the size of the table.

Setting the `result_type` parameter to a pydantic model the result will be deserialized into the given model. Otherwise a dict will be returned. 

```python
table_id = 23

# Get the first 20 person of the table as a dict.
first_20_person = await client.list_table_rows(table_id, True, size=20)

# Get all person where the field name contains the substring »Dave« or »Ann«.
ann_dave_person = await client.list_table_rows(
  table_id,
  True,
  filter=OrFilter().contains("Name", "Dave").contains("Name", "Ann"),
)

# Get all entries of the table. This can take a long time.
all_person = await client.list_all_table_rows(table_id, True, result_type=Person)
```


### Create Table Row(s)

This methods facilitates the creation [of one](https://72nd.github.io/baserowdantic/baserow/client.html#Client.create_row) or [multiple records](https://72nd.github.io/baserowdantic/baserow/client.html#Client.create_rows) in a specific table, identified by its ID. Data for the records can be provided either as a dictionary or as an instance of a `BaseModel`. This flexibility allows users to choose the format that best suits their needs, whether it's a simple dictionary for less complex data or a `BaseModel` for more structured and type-safe data handling.

To create multiple records at once, you can use the `Client().create_rows()` method. This uses Baserow's batch functionality and thus minimizes the number of API calls required to one.

```python
table_id = 23
# Create on new row.
client.create_row(table_id, {"Name": "Ann"}, True)

# Create multiple rows in one go.
client.create_rows(
  table_id,
  [
    Person(name="Tom", age=23),
    Person(name="Anna", age=42),
  ],
  True,
)
```


### Update Table Row

[This method](https://72nd.github.io/baserowdantic/baserow/client.html#Client.update_row) updates a specific row (entry) within a table. Both the table and the row are identified by their unique IDs. The data for the update can be provided either as a Pydantic model or as a dictionary.

- Using a Dictionary: More commonly, a dictionary is used for targeted updates, allowing specific fields within the row to be modified. This method makes more sense in most cases where only certain fields need adjustment, rather than a full update.
- Using a Pydantic Model: When a Pydantic model is used, all values present within the model are applied to the row. This approach is comprehensive, as it updates all fields represented in the model.

```python
table_id = 23
row_id = 42

# Change the name and age of the Row with ID 42 within the table with the ID 23.
rsl = await client.update_row(
  table_id,
  row_id,
  {"Name": "Thomas Niederaichbach", "Age": 29},
  True,
)
print(rsl)
```

The method returns the complete updated row.


### Upload a file

In the [`File` field type](https://72nd.github.io/baserowdantic/baserow/field.html#File), files can be stored. For this purpose, the file must first be uploaded to Baserow's storage. This can be done either with a local file read using open(...) or with a file accessible via a public URL. The method returns a `field.File` instance with all information about the uploaded file.

After the file is uploaded, it needs to be linked to the field in the table row. For this, either the complete `field.File` instance can be passed to the File field or simply an object containing the name ([`field.File.name`](https://72nd.github.io/baserowdantic/baserow/field.html#File.name), the name is unique in any case). The updated row data is then updated to Baserow.

```python
# Upload a local file.
with open("my-image.png", "rb") as file:
  local_rsl = await client.upload_file(file)

# Upload a file accessible via a public URL.
url_rsl = await client.upload_file_via_url("https://picsum.photos/500")

# Set image by passing the entire response object. Caution: this will overwrite
# all previously saved files in the field.
table_id = 23
row_id = 42
file_field_name = "Contract"
await client.update_row(
    table_id,
    row_id,
    {file_field_name: FileField([local_rsl]).model_dump(mode="json")},
    True
)

# Set image by passing just the name of the new file. Caution: this will overwrite
# all previously saved files in the field.
await GlobalClient().update_row(
  table_id,
  row_id,
  {file_field_name: [{"name": url_rsl.name}]},
  True
)
```

### Delete Table Row(s)

[This method](https://72nd.github.io/baserowdantic/baserow/client.html#Client.delete_row) is used to delete one or more rows within a specified table. Both the table and the row are identified by their unique IDs.

```python
table_id = 23

# Delete the row with ID 23
await client.delete_row(table_id, 23)

# Delete rows with ID 29 and 31 in one go.
await client.delete_row(table_id, [29, 31])
```

On success the method returns `None` otherwise an exception will be thrown.


### Create Database Tables

[This method](https://72nd.github.io/baserowdantic/baserow/client.html#Client.create_database_table) facilitates the creation of a new table within a specified database, identified by the unique ID of the database. A human-readable name for the table must be provided. It's also possible to integrate the table creation action into the undo tree of a client session or an action group. This can be accomplished using optional parameters provided in the method.

For additional details on these optional parameters and other functionalities, please refer to the code documentation of this package and the Baserow documentation.

```python
database_id = 19

# Create a new table with the name »Cars« in the database with the ID 19.
await client.create_database_table(database_id, "Cars")
```

### List Tables in Database

[This method](https://72nd.github.io/baserowdantic/baserow/client.html#Client.list_database_tables) retrieves a list of all tables within a specified database. The result includes essential information about each table, such as its ID and name.

```python
database_id = 19

# List all tables within the database with the ID 19.
rsl = await client.list_database_table(database_id)
print(rsl)
```


### Create, Update and Delete Table Fields

The Client class supports the [creation](https://72nd.github.io/baserowdantic/baserow/client.html#Client.create_database_table_field), [updating](https://72nd.github.io/baserowdantic/baserow/client.html#Client.update_database_table_field), and [deletion](https://72nd.github.io/baserowdantic/baserow/client.html#Client.delete_database_table_field) of table fields (referred to as 'Rows').

For both creating and updating a field, the appropriate instance of [`FieldConfigType`](https://72nd.github.io/baserowdantic/baserow/field_config.html#FieldConfigType) is provided. For each field type in Baserow, there is a corresponding field config class that supports the specific settings of the field.

To modify selected properties of an existing field, the configuration of the field can be retrieved using [`Client().list_fields()`](https://72nd.github.io/baserowdantic/baserow/client.html#Client.list_fields), the resulting object can then be modified and subsequently updated.


```python
table_id = 23

# Adds a new text field (»row«) to the person table with the name pronoun.
client.create_database_field(
  table_id,
  TextFieldConfig(name"Pronoun")
)
```


## ORM-like access using models

**Note:** This former part of the README was removed in favor of a more in dept introduction example, the [comprehensive ORM example](https://github.com/72nd/baserowdantic/blob/main/example/orm.py) and more examples in the API documentation.

