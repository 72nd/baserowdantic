# baserowdantic

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
    <li><b>Field-name</b> Type.</li>
    <li><b>Field-name</b> Type.</li>
  </ul>
</details>
<details>
  <summary>Company</summary>
  <ul>
    <li><b>Field-name</b> Type.</li>
    <li><b>Field-name</b> Type.</li>
  </ul>
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
```

### Singleton Client

In many applications, there is a consistent connection to a single Baserow instance throughout the runtime. For performance reasons, it is optimal to use only one session, thus a single client instance. This package includes a client with singleton functionality, which means the singleton only needs to be configured once using `SingletonClient.configure()`. After configuration, the same instance of the client is used consistently. The usage of the `configure()` class method is analog to the initialization method of Client().

```python
from baserow import SingletonClient
```

This setup ensures that your application maintains optimal performance by reusing the same client instance, minimizing the overhead associated with establishing multiple connections or instances.

## Basic Client

Even though Baserowdantic focuses on interacting with Pydantic using Pydantic data models, the Client class used can also be directly employed. The Client class provides CRUD (create, read, update, delete) operations on a Baserow table. It is entirely asynchronous.


### Count Table Rows

This method returns the number of rows or records in a Baserow table. Filters can be optionally passed as parameters.

```python
from baserow import Client, AndFilter

client = Client("baserow.example.com", "<API-TOKEN>")

total_count = await client.table_row_count(1000)
dave_count = await client.table_row_count(
    1000,
    filter=AndFilter().contains("Name", "Dave"),
)
print(f"Total persons: {total_count}, persons called Dave: {dave_count}")

client.close()
```


### List Table Rows

The method reads the entries or records of a table in Baserow. It is possible to filter, sort, select one of the pages (Baserow API uses paging), and determine the number (size) of returned records (between 1 to 200). If it is necessary to retrieve all entries of a table, the method list_all_table_rows exists for this purpose. This method should be used with caution, as many API calls to Baserow may be triggered depending on the size of the table.

```python
from baserow import Client, AndFilter

rsl 

client.close()
```


### Singleton