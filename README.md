# baserowdantic

This package provides a [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) (Create, Read, Update, Delete) client for [Baserow](https://baserow.io/), an open-source alternative to Airtable. Baserow offers a spreadsheet-like interface in the browser for accessing a relational database. Currently, there are numerous (partial) implementations of the Baserow API in Python. baserowdantic emerged from our specific needs and aims to achieve the following:

- Support CRUD operations on Baserow tables.
- Always validate data and benefit from the many conveniences of [Pydantic](https://pydantic.dev/).
- Be fully asynchronous.

As such, it is quite opinionated and supports only a small subset of the API. Users seeking more functionality may consider alternatives like the [python-baserow-client](https://github.com/NiklasRosenstein/python-baserow-client). Interaction with Baserow is facilitated through the definition of Pydantic models, ensuring data validation. The library is written to be fully asynchronous, integrating well with frameworks such as [FastAPI](https://fastapi.tiangolo.com/).


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
```

### List Table Rows