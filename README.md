<p align="right">
  <img src="misc/toc-indicator-dark.svg" width="200" alt="table of contents button hint">
</p>
<p align="center">
  <img src="misc/town.png" alt="AI-generated image of an old town with a prominent town sign reading ‘Baserow’ on it." height="200">
</p>

# baserowdantic

**Caution:** This project is in active development and should currently be considered alpha. Therefore, bugs and (fundamental) breaking changes to the API can occur at any time.

This package provides a [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) (Create, Read, Update, Delete) client for [Baserow](https://baserow.io/), an open-source alternative to Airtable. Baserow offers a spreadsheet-like interface in the browser for accessing a relational database. Currently, there are numerous (partial) implementations of the Baserow API in Python. baserowdantic emerged from our specific needs and aims to achieve the following:

- Support CRUD operations on Baserow tables.
- Always validate data and benefit from the many conveniences of [Pydantic](https://pydantic.dev/).
- Be fully asynchronous.

As such, it is quite opinionated and supports only a small subset of the API. Users seeking more functionality may consider alternatives like the [python-baserow-client](https://github.com/NiklasRosenstein/python-baserow-client). Interaction with Baserow is facilitated through the definition of Pydantic models, ensuring data validation. The library is written to be fully asynchronous, integrating well with frameworks such as [FastAPI](https://fastapi.tiangolo.com/).

The package can be used in two different ways:

1. [Direct Editing with API Basic Client](#basic-client): You can directly edit with Baserow using the API Basic Client.
2. [Executing Actions on a Pydantic Model](#orm-like-access-using-models): Actions can be executed on a pydantic model. In this case, the table structure only needs to be defined once, and the library uses this information for all actions such as creating tables, reading and writing entries, and more.

## Demo / Introduction Example

Still unsure what this is all about? Here's an example to give you a first impression of using baserowdantic:

The example models a simplified version of a library database. There is a table of authors and a table of books. The books table references the corresponding author's entry and can store the cover image. This example is also available as a file [here](example/basic_orm.py).

```python
```

## Note on the Examples Provided

The code snippets demonstrated in this README assume a specific database structure, which consists of two tables: Person and Company. The examples are designed to utilize every field type available in Baserow, providing a comprehensive illustration of its capabilities. The sample data used here can be found in the examples directory and is importable into Baserow for your own experimentation. Please note that in the sample data, there are no Multiselect fields containing more than one item. You can expand the sections below to view the fields defined in each of the two tables.

<details>
  <summary>Person</summary>
  <ul>
    <li><b>Name</b> TextFieldConfig</li>
    <li><b>Age</b> NumberFieldConfig</li>
    <li><b>CV</b> LongTextFieldConfig</li>
    <li><b>Former Employers</b> LinkFieldConfig</li>
    <li><b>NDA Signed</b> BooleanFieldConfig</li>
    <li><b>Employed since</b> DateFieldConfig</li>
    <li><b>Rating</b> RatingFieldConfig</li>
    <li><b>Last modified</b> LastModifiedFieldConfig</li>
    <li><b>Last modified by</b> LastModifiedByFieldConfig</li>
    <li><b>Created on</b> CreatedOnFieldConfig</li>
    <li><b>Created by</b> CreatedByFieldConfig</li>
    <li><b>Workhours per day</b> DurationFieldConfig</li>
    <li><b>Personal Website</b> URLFieldConfig</li>
    <li><b>E-Mail</b> EMailFieldConfig</li>
    <li><b>Contract</b> FileFieldConfig</li>
    <li><b>State</b> SingleSelectFieldConfig</li>
    <li><b>Qualifications</b> MultipleSelectFieldConfig</li>
    <li><b>Phone</b> PhoneNumberFieldConfig</li>
    <li><b>Formula</b> FormulaFieldConfig</li>
    <li><b>Rollup</b> RollupFieldConfig</li>
    <li><b>Names Former Employers</b> LookupFieldConfig</li>
    <li><b>Collaborators</b> MultipleCollaboratorsFieldConfig</li>
    <li><b>UUID</b> UUIDFieldConfig</li>
    <li><b>Autonumber</b> AutonumberFieldConfig</li>
    <li><b>Password</b> PasswordFieldConfig</li>
  </ul>
</details>
<details>
  <summary>Company</summary>
  <ul>
    <li><b>Name</b> TextFieldConfig</li>
    <li><b>E-Mail</b> EMailFieldConfig</li>
    <li><b>Person</b> LinkFieldConfig</li>
  </ul>
</details>

The example code provided frequently references two specific data models: `Person` and `Company`. You can find the `baserow.Table` Model definition in [examples/model.py](examples/model.py).


## Obtaining a Client

The [`Client`](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client) manages the actual HTTP calls to the Baserow REST API. It can be used directly or, ideally, through the model abstraction provided by Pydantic, which is the primary purpose of this package.

### Authentication

Access to the Baserow API requires authentication, and there are [two methods available](https://baserow.io/docs/apis/rest-api) for this:

- **Database Tokens:** These tokens are designed for delivering data to frontends and, as such, can only perform CRUD (Create, Read, Update, Delete) operations on a database. New tokens can be created in the User Settings, where their permissions can also be configured. For instance, it is possible to create a token that only allows reading. These tokens have unlimited validity.
- **JWT Tokens:** All other functionalities require a JWT token, which can be obtained by providing login credentials (email address and password) to the Baserow API. These tokens have a limited lifespan of 10 minutes.

The client in this package can handle both types of tokens. During initialization, you can provide either a Database Token or the email address and password of a user account. For most use cases, the Database Token is sufficient and recommended. The JWT Token is required only for creating new tables or fields within them. For long-running applications, the Database Token is essential since this package currently does not implement refreshing of JWT Tokens.

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

### Singleton/Global Client

In many applications, maintaining a consistent connection to a single Baserow instance throughout the runtime is crucial. To facilitate this, the package provides a [Global Client](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#GlobalClient), which acts as a singleton. This means the client needs to be configured just once using GlobalClient.configure(). After this initial setup, the Global Client can be universally accessed and used throughout the program.

When utilizing the ORM functionality of the table models, all methods within the table models inherently use this Global Client. Please note that the Global Client **can only be configured once**. Attempting to call the [`GlobalClient.configure()`](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#GlobalClient.configure) method more than once will result in an exception. 

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

Even though Baserowdantic focuses on interacting with Pydantic using Pydantic data models, the Client class used can also be directly employed. The [Client class](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client) provides CRUD (create, read, update, delete) operations on a Baserow table. It is entirely asynchronous.


### Count Table Rows

[This method](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.table_row_count) returns the number of rows or records in a Baserow table. Filters can be optionally passed as parameters.

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

[This function](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.list_fields) retrieves the fields (also known as rows) present in a specified table along with their configurations. The return value contains the information in the form of the `FieldConfig` model.

```python
table_id = 23
print(await client.list_fields(table_id))
```


### List Table Rows

[The method](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.list_table_rows) reads the entries or records of a table in Baserow. It is possible to filter, sort, select one of the pages (Baserow API uses paging), and determine the number (size) of returned records (between 1 to 200). If it is necessary to retrieve all entries of a table, the method [`Client().list_all_table_rows`](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.list_table_rows) exists for this purpose. This method should be used with caution, as many API calls to Baserow may be triggered depending on the size of the table.

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

This methods facilitates the creation [of one](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.create_row) or [multiple records](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.create_rows) in a specific table, identified by its ID. Data for the records can be provided either as a dictionary or as an instance of a `BaseModel`. This flexibility allows users to choose the format that best suits their needs, whether it's a simple dictionary for less complex data or a `BaseModel` for more structured and type-safe data handling.

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

[This method](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.update_row) updates a specific row (entry) within a table. Both the table and the row are identified by their unique IDs. The data for the update can be provided either as a Pydantic model or as a dictionary.

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

In the [`File` field type](https://alex-berlin-tv.github.io/baserowdantic/baserow/field.html#File), files can be stored. For this purpose, the file must first be uploaded to Baserow's storage. This can be done either with a local file read using open(...) or with a file accessible via a public URL. The method returns a `field.File` instance with all information about the uploaded file.

After the file is uploaded, it needs to be linked to the field in the table row. For this, either the complete `field.File` instance can be passed to the File field or simply an object containing the name ([`field.File.name`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field.html#File.name), the name is unique in any case). The updated row data is then updated to Baserow.

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

[This method](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.delete_row) is used to delete one or more rows within a specified table. Both the table and the row are identified by their unique IDs.

```python
table_id = 23

# Delete the row with ID 23
await client.delete_row(table_id, 23)

# Delete rows with ID 29 and 31 in one go.
await client.delete_row(table_id, [29, 31])
```

On success the method returns `None` otherwise an exception will be thrown.


### Create Database Tables

[This method](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.create_database_table) facilitates the creation of a new table within a specified database, identified by the unique ID of the database. A human-readable name for the table must be provided. It's also possible to integrate the table creation action into the undo tree of a client session or an action group. This can be accomplished using optional parameters provided in the method.

For additional details on these optional parameters and other functionalities, please refer to the code documentation of this package and the Baserow documentation.

```python
database_id = 19

# Create a new table with the name »Cars« in the database with the ID 19.
await client.create_database_table(database_id, "Cars")
```

### List Tables in Database

[This method](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.list_database_tables) retrieves a list of all tables within a specified database. The result includes essential information about each table, such as its ID and name.

```python
database_id = 19

# List all tables within the database with the ID 19.
rsl = await client.list_database_table(database_id)
print(rsl)
```


### Create, Update and Delete Table Fields

"The Client class supports the [creation](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.create_database_table_field), [updating](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.update_database_table_field), and [deletion](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.delete_database_table_field) of table fields (referred to as 'Rows')."

For both creating and updating a field, the appropriate instance of [`FieldConfigType`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field_config.html#FieldConfigType) is provided. For each field type in Baserow, there is a corresponding field config class that supports the specific settings of the field.

To modify selected properties of an existing field, the configuration of the field can be retrieved using [`Client().list_fields()`](https://alex-berlin-tv.github.io/baserowdantic/baserow/client.html#Client.list_fields), the resulting object can then be modified and subsequently updated.


```python
table_id = 23

# Adds a new text field (»row«) to the person table with the name pronoun.
client.create_database_field(
  table_id,
  TextFieldConfig(name"Pronoun")
)
```


## ORM-like access using models

The main motivation behind baserowdantic is to handle »everyday« CRUD (Create, Read, Update, Delete) interactions with Baserow through a model derived from pydantic's BaseModel called [`Table`](https://alex-berlin-tv.github.io/baserowdantic/baserow/table.html#Table). This Table model defines the structure and layout of a table in Baserow at a single location, thereby enabling validation of both input and output.

The concept is straightforward: at a single point within the application, the data structure's layout in Baserow is defined within the Table model. Based on this model, the table can be created in Baserow, and all operations on the table can be performed. This approach also simplifies the deployment of applications that use Baserow as a backend, as it automatically sets up the required data structure during a new installation. Additionally, the validation functionalities ensure that the structure in the Baserow database matches the application's expectations.

Contrary to what the name 'Table' suggests, an instance of it with data represents only a single row.


### Configure the model

In order for a Table instance to interact with Baserow, it must first be configured using ClassVars.

```python
from baserow.table import Table
from pydantic import ConfigDict


class Company(Table):
    table_id = 23
    table_name = "Company"
    model_config = ConfigDict(populate_by_name=True)
```

The following properties need to be set:

- [`table_id`](https://alex-berlin-tv.github.io/baserowdantic/baserow/table.html#Table.table_id): The unique ID of the Baserow table where the data represented by the model is stored. If the table does not yet exist and needs to be created, this attribute does not need to be set initially.
- [`table_name`](https://alex-berlin-tv.github.io/baserowdantic/baserow/table.html#Table.table_name): A human-readable name for the table. This information is used when creating the table on Baserow and also aids in understanding debug outputs.
- [`populate_by_name`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.populate_by_name): This Pydantic setting must be enabled with `model_config = ConfigDict(populate_by_name=True)`, as the ORM logic will not function without it.

The methods of the model check whether the configuration is correct before executing any operations. If it is not, a [`InvalidTableConfigurationError`](https://alex-berlin-tv.github.io/baserowdantic/baserow/error.html#InvalidTableConfigurationError) is thrown.


### Define the model fields

The definition of fields in a table is done in a manner similar to what is [expected from Pydantic](https://docs.pydantic.dev/latest/concepts/fields/). Whenever possible, the values of the fields are de-/serialized to/from Python's built-in types. The value of a text field is converted to a `str`, a number field is serialized to an `int` or `float`, and a date field to a `datetime.datetime` object. In certain cases, the data type of the field values is more complex than can be represented by a built-in data type. This is the case, for example, with [File](https://alex-berlin-tv.github.io/baserowdantic/baserow/field.html#File) or [Single-Select](https://alex-berlin-tv.github.io/baserowdantic/baserow/field.html#SingleSelectField) fields. The definitions for these field values can be found in the [`field`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field.html) module.

```python
from typing import Optional

from baserow.table import Table
from pydantic import ConfigDict

class Company(Table):
    table_id = 23
    table_name = "Company"
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias=str("Name"))
    email: Optional[str] = Field(default=None, alias=str("E-Mail"))
```

Every row in Baserow includes the field id, which contains the unique ID of the row. This field is already defined as [`row_id`](https://alex-berlin-tv.github.io/baserowdantic/baserow/table.html#RowLink.row_id) in the Table model.

In Baserow, a field has a type in addition to its value. The type of field cannot always be inferred from the value alone. For instance, a value of type `str` appear in both a Short Text Field and Long Text Field. Certain field types have even more configurable settings available. For example, a rating field might require specifying the color and shape of the rating scale. Similarly, for Single or Multiple Select Fields, the possible options must be defined. These configurations are managed through what are known as field configs, summarized under [`FieldConfigType`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field_config.html#FieldConfigType). By using type annotations of a field config encapsulated in a [`Config`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field_config.html#Config) wrapper, it is possible to configure the desired field type and its properties. All available field configs can be found in the [`field_config`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field_config.html) module.

Furthermore, it is necessary for each table to have **exactly one primary field**. This is defined by passing an instance of [`PrimaryField`](https://alex-berlin-tv.github.io/baserowdantic/baserow/field_config.html#PrimaryField) to a field via typing annotations.

```python
from typing import Annotated, Optional

from baserow.field_config import Config, LongTextFieldConfig, PrimaryField
from baserow.table import Table
from pydantic import ConfigDict


class Person(Table):
    # Table config omitted.

    name: Annotated[
        str,
        Field(alias=str("Name")),
        PrimaryField(),
    ]
    cv: Annotated[
        Optional[str],
        Config(LongTextFieldConfig(long_text_enable_rich_text=True)),
        Field(alias=str("CV")),
    ]
```

In this example, you can observe several things:

- The `name` field is declared as the primary field.
- The `cv` field is configured as a long text field with rich text formatting enabled.

Subsequently, a variety of fields and their configurations will be introduced.


#### Link field

In Baserow, the Link field allows linking a record of one table with record(s) from another table. Baserowdantic not only offers an ergonomic configuration of these relationships but also provides easy access to the linked records (which can even be cached, if desired). Let's consider an example:

```python
from typing import Annotated, Optional

from baserow.field_config import Config, PrimaryField
from baserow.table import Table, TableLinkField
from pydantic import ConfigDict


class Company(Table):
    table_id = 23
    table_name = "Company"
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias=str("Name"))
    email: Optional[str] = Field(default=None, alias=str("E-Mail"))


class Person(Table):
    table_id = 42
    table_name = "Person"
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias=str("Name"))
    former_employees: Optional[TableLinkField[Company]] = Field(
        default=None,
        alias=str("Former Employers"),
    )
```

In this example, each entry in the People table can refer to entries in the Company table. The model can now be used as follows:

```python

```

#### File field

The File field in Baserow can store one or more files (attachments).

TODO.


#### Single and multiple select field

TODO.

### Validate

TODO.


### Create a table

TODO.


### Query a table

A model can be validated against a table to ensure that the defined table model corresponds to the table in Baserow. The following checks are performed:

- Whether all fields defined in the model with the same name and type are present in the Baserow table. If not, an `error.FieldNotInBaserowTableError` or `error.FieldTypeDiffersError` is thrown.
- Whether all fields present in the Baserow table are also defined in the model.

TODO.


### Get by ID

TODO.


### Create a row

TODO.


### Update a row

TODO: Single by ID.

TODO: Single with instance.


### Delete a row

TODO.