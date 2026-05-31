# list_project_api_access_requests 実装計画

## 目的

Project owner、API 審査者、Hub 管理者が、Project 内の利用申請履歴を確認できるようにする。

## 方針

- Project 単位の申請履歴を状態、対象 API、申請者、審査者、日時で確認できるようにする。
- role に応じて参照可能な request を絞り込む。
- 一覧は pagination を前提にする。
- unit test では SQLite in-memory で権限別、状態別、ページングを検証する。

## 実装計画

1. Project ID と一覧取得条件を検証する。
2. 対象 Project を取得する。
3. 呼び出し元が Project owner、対象 API reviewer、Hub 管理者のいずれかであることを確認する。
4. Project に紐づく access request を検索する。
5. 対象 API、申請者、審査者、状態、審査結果を取得する。
6. `limit` と `nextToken` を適用する。
7. 申請履歴一覧を返す。

## 作業

- 利用申請一覧 API の contract、response schema、router を実装する。
- Project owner、reviewer、admin の参照条件を SQL に反映する。
- 状態、対象 API、審査結果の response 整形を実装する。
- pagination と nextToken 生成を実装する。
- 権限別、状態別、ページングの単体テストを作成する。

## 完了条件

- `GET /projects/{projectId}/api-access-requests` で申請履歴を取得できる。
- owner/reviewer/admin の参照範囲が分かれている。
- 申請状態の追跡に必要な情報を返す。
