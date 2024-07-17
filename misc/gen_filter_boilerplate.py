"""
Generate part of the filter.py module based on the table in the
API-documentation.
"""
import csv


# Read the CSV file
filters = []
with open('filters.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        if 'deprecated' not in row['Filter']:
            filters.append(row)


# Generate FilterMode Enum class
filter_mode_class = """class FilterMode(str, Enum):
    \"""
    The filter type (also called mode) defines the behavior of the filter,
    determining how the filter value is applied to the field. Naming follows the
    Baserow UI convention and therefore may differ from the values in some
    instances.
    \"""
"""

for filter in filters:
    filter_name = filter['Filter'].upper().replace(' ', '_')
    filter_mode_class += f"    {filter_name} = \"{filter_name.lower()}\"\n"

filter_mode_class += "\n\n"

# Generate Filter class
filter_class = """class Filter(BaseModel):
    \"""
    A filter tree allows for the construction of complex filter queries. The
    object serves as a container for individual filter conditions, all of which
    must be true (AND) or at least one must be true (OR).
    \"""
    operator: str = Field(alias="filter_type")
    conditions: List['Condition'] = Field(default=[], alias="filters")
"""

# Generate methods for the Filter class
for filter in filters:
    method_name = filter['Filter'].lower().replace(' ', '_')
    filter_class += f"""
    def {method_name}(self, field: Union[int, str], value: Optional[str]) -> Self:
        \"""
        Adds a condition with {method_name} to the filter.
        \"""
        self.conditions.append(
            Condition(field=field, mode=FilterMode.{filter['Filter'].upper().replace(' ', '_')}, value=value),
        )
        return self
"""

# Combine all generated classes into one script
full_script = filter_mode_class + filter_class

# Print the generated script
print(full_script)
