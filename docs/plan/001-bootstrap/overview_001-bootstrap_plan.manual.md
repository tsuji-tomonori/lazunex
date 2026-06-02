# 001-bootstrap 実装計画

## 目的

Lazunex の初期構築として、社内 API Hub の管理 API、DB、認証・認可、AWS 反映、仕様生成の土台を実装可能な状態にする。

## 方針

- 管理 API は FastAPI で実装し、将来の API Gateway REST API + Lambda 配置を前提にする。
- Runtime API は既存の API Gateway REST API を対象とし、Lazunex は公開登録、利用申請、承認、Cognito/App Client/Usage Plan 反映を担当する。
- UI は初期範囲外とし、管理 API を直接利用できる状態を優先する。
- DB は SQL を一次情報にし、実装、CRUD、Query 仕様の対応関係を追跡できるようにする。
- 外部リソース操作は integrations/resource 境界に閉じ、unit test では fake client と SQLite in-memory で検証できる構造にする。
- 変更系 API は `Idempotency-Key` を前提にし、AWS 反映の途中経過を operation/step として記録する。
- API key と client secret は平文保持せず、ハッシュ、hash key version、末尾情報だけを DB に残す。

## 実装計画

1. FastAPI、設定、DB session、migration、test fixture、Docker/Compose の開発基盤を整える。
2. API、Project、Access Request、Subscription、Provisioning、Audit のテーブルを作成する。
3. SQL を手書きし、query 呼び出しと CRUD 仕様を対応付ける。
4. API 単位の contract、router、schema、SQL 配置を固定する。
5. Cognito と API Gateway の操作を resource integration として抽象化する。
6. API 公開登録の処理フローを実装する。
7. Project 作成の処理フローを実装する。
8. 利用申請作成の処理フローを実装する。
9. 承認・却下の処理フローを実装する。
10. API/Project/利用権の参照系処理フローを実装する。
11. 仕様生成、CRUD 表、unit test、docs check を CI で確認できる状態にする。

## 作業

- FastAPI アプリケーション、DB 接続、migration、Docker/Compose を整備する。
- 初期対象 API の contract、schema、router、SQL を実装する。
- Cognito と API Gateway の resource integration と fake client を実装する。
- API 単位の単体テストを作成する。
- SQLite in-memory と fake integration で unit test を実行できるようにする。
- 生成仕様と手書き docs の更新ルールを整える。

## 実装状況

- API Gateway stage/method 読み取りと method 更新、Cognito resource server 読み取り、Cognito App Client の token/rotation/OAuth 設定 DTO を resource integration に追加済み。
- 利用申請作成と却下は、router から `CallerIdentity`、DB session、request context を渡し、生成済み query による DB 保存まで接続済み。
- 利用申請承認は、DB から AWS ID と scope を解決して API Gateway / Cognito へ渡す経路と、主要な承認結果テーブル保存まで接続済み。
- 全 `_sequence_placeholder` の削除は未完了。未接続範囲は、既存 idempotency record の read/replay、承認後段 event 永続化、`createProject` の DB 永続化全体、`publishApi` / `updateProjectPublicClient` の catalog/provisioning/audit metadata 保存である。

## 完了条件

- 初期対象 API の plan、spec、SQL、test 方針が揃っている。
- unit test は SQLite in-memory と fake integration で実行できる。
- Docker Compose でローカル API と MySQL を起動できる。
- 変更系 API の冪等性、監査、AWS 反映記録の実装方針がコードに反映されている。
