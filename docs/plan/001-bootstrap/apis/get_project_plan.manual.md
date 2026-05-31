# get_project 実装計画

## 目的

Project owner または Hub 管理者が、Project 詳細、API key metadata、Usage Plan、Cognito App Client 設定概要を確認できるようにする。

## 方針

- Project の基本情報と払い出し済み AWS resource ID を返す。
- API key 値と client secret 値は返さない。
- Project owner 以外の参照は認可で制御する。
- unit test では SQLite in-memory で secret 非表示と参照制御を検証する。

## 実装計画

1. Project ID を検証する。
2. 対象 Project を取得する。
3. 呼び出し元が Project owner または Hub 管理者であることを確認する。
4. API key metadata を取得する。
5. Usage Plan metadata を取得する。
6. Cognito App Client metadata を取得する。
7. secret 値を含めずに response を整形する。
8. Project 詳細を返す。

## 作業

- Project 詳細取得 API の contract、response schema、router を実装する。
- Project、owner、API key metadata、Usage Plan、App Client metadata の SQL を実装する。
- secret 非表示の response 整形を実装する。
- Project owner と Hub 管理者の参照制御を実装する。
- 正常系、権限不足、not found、secret 非表示の単体テストを作成する。

## 完了条件

- `GET /projects/{projectId}` で Project 詳細を取得できる。
- secret 値が response に含まれない。
- owner/admin の参照制御が実装されている。
