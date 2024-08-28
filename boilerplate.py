import json
from typing import Tuple

payload_keys = [
    "key1",
    "key2",
]


def test_function(*args, **kwargs) -> Tuple[int, str, dict]:
    result = {}

    return 200, "Success", result


def lambda_handler(event, context):
    body = json.loads(event["body"])

    for key in payload_keys:
        if key not in body:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "message": f"Missing key: {key}",
                    }
                ),
            }

    status_code, message, result = test_function(**body)

    return {
        "statusCode": status_code,
        "body": json.dumps({"message": message, "data": result}, ensure_ascii=False),
    }


if __name__ == "__main__":
    event = {
        "body": json.dumps(
            {
                "key1": "value1",
                "key2": "value2",
            }
        )
    }
    print(lambda_handler(event, None))
