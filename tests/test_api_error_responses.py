from app.main import create_app


def test_api_error_responses_are_selected_per_operation() -> None:
    schema = create_app().openapi()
    expected_statuses = {
        "listApis": {"200", "401", "403", "422", "429", "500"},
        "getApi": {"200", "401", "403", "404", "422", "429", "500"},
        "publishApi": {"201", "400", "401", "403", "409", "422", "429", "500", "502", "503"},
        "listProjects": {"200", "401", "403", "422", "429", "500"},
        "createProject": {
            "201",
            "400",
            "401",
            "403",
            "409",
            "422",
            "429",
            "500",
            "502",
            "503",
        },
        "getProject": {"200", "401", "403", "404", "422", "429", "500"},
        "listProjectSubscriptions": {"200", "401", "403", "422", "429", "500"},
        "listProjectApiAccessRequests": {
            "200",
            "401",
            "403",
            "422",
            "429",
            "500",
        },
        "createApiAccessRequest": {
            "201",
            "400",
            "401",
            "403",
            "404",
            "409",
            "422",
            "429",
            "500",
            "503",
        },
        "updateProjectPublicClient": {
            "200",
            "400",
            "401",
            "403",
            "404",
            "409",
            "422",
            "429",
            "500",
            "502",
            "503",
        },
        "approveApiAccessRequest": {
            "200",
            "401",
            "403",
            "404",
            "409",
            "422",
            "429",
            "500",
            "502",
            "503",
        },
        "rejectApiAccessRequest": {
            "200",
            "400",
            "401",
            "403",
            "404",
            "409",
            "422",
            "429",
            "500",
            "503",
        },
    }

    actual_statuses = {
        operation["operationId"]: set(operation["responses"])
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if operation.get("operationId") in expected_statuses
    }

    assert actual_statuses == expected_statuses


def test_api_error_response_descriptions_explain_when_they_occur() -> None:
    schema = create_app().openapi()
    expected_phrases = {
        "400": "業務ルール",
        "401": "認証情報",
        "403": "権限",
        "404": "存在しない",
        "409": "競合",
        "422": "OpenAPIスキーマ",
        "429": "上限",
        "500": "想定外",
        "502": "外部AWSサービス",
        "503": "一時的に利用できない",
    }

    for path_item in schema["paths"].values():
        for operation in path_item.values():
            operation_id = operation.get("operationId")
            if operation_id is None:
                continue
            for status_code, expected_phrase in expected_phrases.items():
                if status_code in operation["responses"]:
                    description = operation["responses"][status_code]["description"]
                    assert expected_phrase in description, f"{operation_id} {status_code}"
