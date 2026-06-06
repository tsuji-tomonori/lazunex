from tools.check_api_status_samples import check_api_status_samples


def test_api_status_samples_cover_openapi_statuses_and_match_response_schema() -> None:
    assert check_api_status_samples() == []
