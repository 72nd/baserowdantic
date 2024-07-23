# ORM like functionality

**Will be reworked to be a part of the API.**

The main motivation behind baserowdantic is to handle »everyday« CRUD (Create, Read, Update, Delete) interactions with Baserow through a model derived from pydantic's BaseModel called [`Table`](https://72nd.github.io/baserowdantic/baserow/table.html#Table). This Table model defines the structure and layout of a table in Baserow at a single location, thereby enabling validation of both input and output.

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

- [`table_id`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.table_id): The unique ID of the Baserow table where the data represented by the model is stored. If the table does not yet exist and needs to be created, this attribute does not need to be set initially.
- [`table_name`](https://72nd.github.io/baserowdantic/baserow/table.html#Table.table_name): A human-readable name for the table. This information is used when creating the table on Baserow and also aids in understanding debug outputs.
- [`populate_by_name`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.populate_by_name): This Pydantic setting must be enabled with `model_config = ConfigDict(populate_by_name=True)`, as the ORM logic will not function without it.

The methods of the model check whether the configuration is correct before executing any operations. If it is not, a [`InvalidTableConfigurationError`](https://72nd.github.io/baserowdantic/baserow/error.html#InvalidTableConfigurationError) is thrown.


### Define the model fields

The definition of fields in a table is done in a manner similar to what is [expected from Pydantic](https://docs.pydantic.dev/latest/concepts/fields/). Whenever possible, the values of the fields are de-/serialized to/from Python's built-in types. The value of a text field is converted to a `str`, a number field is serialized to an `int` or `float`, and a date field to a `datetime.datetime` object. In certain cases, the data type of the field values is more complex than can be represented by a built-in data type. This is the case, for example, with [File](https://72nd.github.io/baserowdantic/baserow/field.html#File) or [Single-Select](https://72nd.github.io/baserowdantic/baserow/field.html#SingleSelectField) fields. The definitions for these field values can be found in the [`field`](https://72nd.github.io/baserowdantic/baserow/field.html) module.

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

Every row in Baserow includes the field id, which contains the unique ID of the row. This field is already defined as [`row_id`](https://72nd.github.io/baserowdantic/baserow/table.html#RowLink.row_id) in the Table model.

In Baserow, a field has a type in addition to its value. The type of field cannot always be inferred from the value alone. For instance, a value of type `str` appear in both a Short Text Field and Long Text Field. Certain field types have even more configurable settings available. For example, a rating field might require specifying the color and shape of the rating scale. Similarly, for Single or Multiple Select Fields, the possible options must be defined. These configurations are managed through what are known as field configs, summarized under [`FieldConfigType`](https://72nd.github.io/baserowdantic/baserow/field_config.html#FieldConfigType). By using type annotations of a field config encapsulated in a [`Config`](https://72nd.github.io/baserowdantic/baserow/field_config.html#Config) wrapper, it is possible to configure the desired field type and its properties. All available field configs can be found in the [`field_config`](https://72nd.github.io/baserowdantic/baserow/field_config.html) module.

Furthermore, it is necessary for each table to have **exactly one primary field**. This is defined by passing an instance of [`PrimaryField`](https://72nd.github.io/baserowdantic/baserow/field_config.html#PrimaryField) to a field via typing annotations.

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