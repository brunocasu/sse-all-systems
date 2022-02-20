import jsonschema
from jsonschema import validate
# Describe what kind of json you expect.


class JsonSchemaValidation:
    flow_schema = read_json('json_schema/flow_schema.json')
