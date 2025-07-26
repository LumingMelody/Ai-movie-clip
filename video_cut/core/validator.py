from jsonschema import validate, ValidationError
import json

def validate_json(instance, schema):
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        raise ValueError(f"Schema 校验失败: {e.message}")