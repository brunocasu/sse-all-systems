import jsonschema
from jsonschema import validate

from DevelopmentSystem.utility import read_json


class JsonSchemaValidation:

    def __init__(self, base_dir, system):
        """
            DEVELOPMENT SYSTEM
        """
        if system == "development":
            self.flow_schema = read_json(base_dir + 'json_schema/flow_schema.json')
            self.conf_params_schema = read_json(base_dir + 'json_schema/config_params_schema.json')
            self.validation_report_schema = read_json(base_dir + 'json_schema/validation_report_schema.json')
            self.test_report_schema = read_json(base_dir + 'json_schema/test_report_schema.json')
            self.app_setting_schema = read_json(base_dir + 'json_schema/application_settings_schema.json')

        """
            SEGREGATION SYSTEM
        """
        if system == "segregation":
            self.segregation_conf_schema = read_json(base_dir + "json_schema/conf_schema.json")

    """
    DEVELOPMENT SYSTEM 
    """

    def conf_params_validation(self, json_file):
        try:
            validate(instance=json_file, schema=self.conf_params_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("[DEVELOPMENT SYSTEM]: Invalid Configuration Parameters File Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print(
                "[DEVELOPMENT SYSTEM]: Invalid Schema for Configuration Parameters file validation.\nAdd a valid json "
                "schema.")
            return False

    def validation_report_validation(self, json_file):
        try:
            validate(instance=json_file, schema=self.validation_report_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("[DEVELOPMENT SYSTEM]: Invalid Validation Report File Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print(
                "[DEVELOPMENT SYSTEM]: Invalid Schema for Validation Report File validation.\nAdd a valid json schema.")
            return False

    def flow_validation(self, json_file):
        try:
            validate(instance=json_file, schema=self.flow_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("[DEVELOPMENT SYSTEM]: Invalid Execution Flow File Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print("[DEVELOPMENT SYSTEM]: Invalid Schema for Execution Flow file validation.\nAdd a valid json schema.")
            return False

    def app_settings_validation(self, json_file):
        try:
            validate(instance=json_file, schema=self.app_setting_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("[DEVELOPMENT SYSTEM]: Invalid Application Setting File Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print(
                "[DEVELOPMENT SYSTEM]: Invalid Schema for Application Setting file validation.\nAdd a valid json "
                "schema.")
            return False

    def test_report_validation(self, json_file):
        try:
            validate(instance=json_file, schema=self.test_report_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("[DEVELOPMENT SYSTEM]: Invalid Test Report File Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print("[DEVELOPMENT SYSTEM]: Invalid Json Schema for Test Report validation.\nAdd a valid json schema.")
            return False

    """
        SEGREGATION SYSTEM
    """

    def segregation_conf_file_validation(self, json_file):
        try:
            validate(instance=json_file, schema=self.segregation_conf_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("[SEGREGATION SYSTEM]: Invalid Configuration File Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print(
                "[SEGREGATION SYSTEM]: Invalid Json Schema for Configuration File validation.\n"
                "Add a valid json schema.")
            return False

    """     
        CAN BE USED WITH ANY JSON BY PASSING THE SCHEMA AND THE JSON TO BE VALIDATED.
    """

    def general_validation(self, json_schema, json_file):
        try:
            validate(instance=json_file, schema=json_schema)
            return True
        except jsonschema.exceptions.ValidationError:
            print("Invalid Json Format!\n")
            return False
        except jsonschema.exceptions.SchemaError:
            print("Invalid Json Schema.\nAdd a valid json schema.")
            return False
