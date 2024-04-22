# baserowdantic

**Caution:** This project is in active development and should currently be considered alpha. Therefore, bugs and (fundamental) breaking changes to the API can occur at any time.

This package provides a [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) (Create, Read, Update, Delete) client for [Baserow](https://baserow.io/), an open-source alternative to Airtable. Baserow offers a spreadsheet-like interface in the browser for accessing a relational database. Currently, there are numerous (partial) implementations of the Baserow API in Python. baserowdantic emerged from our specific needs and aims to achieve the following:

- Support CRUD operations on Baserow tables.
- Always validate data and benefit from the many conveniences of [Pydantic](https://pydantic.dev/).
- Be fully asynchronous.

As such, it is quite opinionated and supports only a small subset of the API. Users seeking more functionality may consider alternatives like the [python-baserow-client](https://github.com/NiklasRosenstein/python-baserow-client). Interaction with Baserow is facilitated through the definition of Pydantic models, ensuring data validation. The library is written to be fully asynchronous, integrating well with frameworks such as [FastAPI](https://fastapi.tiangolo.com/).


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

The example code provided frequently references two specific data models: `Person` and `Company`. Definitions and schemas for these models can be found below.

<details>
  <summary>Person</summary>
    ```python
    from baserow import Client
    ```
</details>
<details>
  <summary>Company</summary>
    ```python
    from baserow import Client
    ```
</details>


## Obtaining a Client

The client manages the actual HTTP calls to the Baserow REST API. It can be used directly or, ideally, through the model abstraction provided by Pydantic, which is the primary purpose of this package.

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

In many applications, maintaining a consistent connection to a single Baserow instance throughout the runtime is crucial. To facilitate this, the package provides a Global Client, which acts as a singleton. This means the client needs to be configured just once using GlobalClient.configure(). After this initial setup, the Global Client can be universally accessed and used throughout the program.

When utilizing the ORM functionality of the table models, all methods within the table models inherently use this Global Client. Please note that the Global Client **can only be configured once**. Attempting to call the `configure()` method more than once will result in an exception. 

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

Even though Baserowdantic focuses on interacting with Pydantic using Pydantic data models, the Client class used can also be directly employed. The Client class provides CRUD (create, read, update, delete) operations on a Baserow table. It is entirely asynchronous.


### Count Table Rows

This method returns the number of rows or records in a Baserow table. Filters can be optionally passed as parameters.

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

This function retrieves the fields (also known as rows) present in a specified table along with their configurations. The return value contains the information in the form of the `FieldConfig` model.

```python
table_id = 23
print(await client.list_fields(table_id))
```


### List Table Rows

The method reads the entries or records of a table in Baserow. It is possible to filter, sort, select one of the pages (Baserow API uses paging), and determine the number (size) of returned records (between 1 to 200). If it is necessary to retrieve all entries of a table, the method list_all_table_rows exists for this purpose. This method should be used with caution, as many API calls to Baserow may be triggered depending on the size of the table.

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

This method facilitates the creation of one or more records in a specific table, identified by its ID. Data for the records can be provided either as a dictionary or as an instance of a BaseModel. This flexibility allows users to choose the format that best suits their needs, whether it's a simple dictionary for less complex data or a BaseModel for more structured and type-safe data handling.

To create multiple records at once, you can use the create_rows() method. This uses Baserow's batch functionality and thus minimizes the number of API calls required to one.

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

This method updates a specific row (entry) within a table. Both the table and the row are identified by their unique IDs. The data for the update can be provided either as a Pydantic model or as a dictionary.

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

In the File field type, files can be stored. For this purpose, the file must first be uploaded to Baserow's storage. This can be done either with a local file read using open(...) or with a file accessible via a public URL. The method returns a `field.File` instance with all information about the uploaded file.

After the file is uploaded, it needs to be linked to the field in the table row.  For this, either the complete `field.File` instance can be passed to the File field or simply an object containing the name (`field.File.name`, the name is unique in any case).

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

This method is used to delete one or more rows within a specified table. Both the table and the row are identified by their unique IDs.

```python
table_id = 23

# Delete the row with ID 23
await client.delete_row(table_id, 23)

# Delete rows with ID 29 and 31 in one go.
await client.delete_row(table_id, [29, 31])
```

On success the method returns `None` otherwise an exception will be thrown.


### Create Database Tables

This method facilitates the creation of a new table within a specified database, identified by the unique ID of the database. A human-readable name for the table must be provided. It's also possible to integrate the table creation action into the undo tree of a client session or an action group. This can be accomplished using optional parameters provided in the method.

For additional details on these optional parameters and other functionalities, please refer to the code documentation of this package and the Baserow documentation.

```python
database_id = 19

# Create a new table with the name »Cars« in the database with the ID 19.
await client.create_database_table(database_id, "Cars")
```

### List Tables in Database

This method retrieves a list of all tables within a specified database. The result includes essential information about each table, such as its ID and name.

```python
database_id = 19

# List all tables within the database with the ID 19.
rsl = await client.list_database_table(database_id)
print(rsl)
```


### Create Table Fields

This method is used to add a new field to an existing table, which is identified by its ID. Each call to this method can add one field. You can use any field configuration that is part of the FieldConfigType.


```python
table_id = 23

# Adds a new text field (»row«) to the person table with the name pronoun.
client.create_database_field(
  table_id,
  TextFieldConfig(name"Pronoun")
)
```


## ORM-like access using models

The main motivation behind baserowdantic is to handle »everyday« CRUD (Create, Read, Update, Delete) interactions with Baserow through a model derived from pydantic's BaseModel called Table. This Table model defines the structure and layout of a table in Baserow at a single location, thereby enabling validation of both input and output.


### Configure the model

In order for a Table instance to interact with Baserow, it must first be configured using ClassVars.

TODO.


### Define the model fields

Table fields are defined in the usual Pydantic manner. For more complex field types (such as File, Single Select, etc.), baserowdantic defines its own models.

TODO.


#### Link field

TODO.


#### File field

The File field in Baserow can store one or more files (attachments).

TODO.


#### Single and multiple select field

TODO.

### Validate

TODO.


### Query a table

A model can be validated against a table to ensure that the defined table model corresponds to the table in Baserow. The following checks are performed:

- Whether all fields defined in the model with the same name and type are present in the Baserow table. If not, an error.FieldNotInBaserowTableException or error.FieldTypeDiffersException is thrown.
- Whether all fields present in the Baserow table are also defined in the model.

TODO.


### Get by ID

TODO.


### Get by linked field

TODO.


### Create a row

TODO.


### Update a row

TODO: Single.

TODO: Batch.


### Delete a row

TODO.