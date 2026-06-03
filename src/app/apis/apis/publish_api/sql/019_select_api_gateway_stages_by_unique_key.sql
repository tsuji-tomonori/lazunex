-- API Gateway stageの重複登録を防ぐため、既存stageを取得する。
SELECT
    api_stage_id,
    api_id,
    aws_account_id,
    aws_region,
    apigw_rest_api_id,
    apigw_stage_name
FROM api_gateway_stages
WHERE aws_account_id = @aws_account_id
  AND aws_region = @aws_region
  AND apigw_rest_api_id = @apigw_rest_api_id
  AND apigw_stage_name = @apigw_stage_name;
