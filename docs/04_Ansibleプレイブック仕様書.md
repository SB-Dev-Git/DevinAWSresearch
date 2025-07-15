# Ansibleプレイブック仕様書

## 概要
本ドキュメントでは、DevinAWSresearchシステムで使用されるAnsibleプレイブックの詳細仕様を説明します。

## 1. web_server_setup.yml 仕様

### 1.1 基本情報
- **ファイル名**: web_server_setup.yml
- **目的**: Hello World Node.jsアプリケーションの包括的Webサーバセットアップ
- **対象ホスト**: target_servers
- **実行権限**: become: yes（sudo権限必要）
- **ファクト収集**: gather_facts: yes

### 1.2 変数定義
```yaml
vars:
  app_name: hello-world-webapp
  app_user: nodejs
  app_dir: /opt/{{ app_name }}
  domain_name: "{{ ansible_default_ipv4.address }}"
```

#### 変数説明
- **app_name**: アプリケーション名（systemdサービス名にも使用）
- **app_user**: Node.jsアプリケーション実行用の専用ユーザー
- **app_dir**: アプリケーションインストールディレクトリ
- **domain_name**: Nginx設定で使用するドメイン名（IPアドレス使用）

### 1.3 タスク詳細仕様

#### 1.3.1 システム更新・基本パッケージインストール

**タスク1: システムパッケージ更新**
```yaml
- name: システムパッケージ更新
  yum:
    name: "*"
    state: latest
```
- **モジュール**: yum
- **処理内容**: 全システムパッケージを最新版に更新
- **実行時間**: 環境により5-15分

**タスク2: Gitインストール**
```yaml
- name: Gitインストール
  yum:
    name: git
    state: present
```
- **モジュール**: yum
- **処理内容**: Gitバージョン管理システムのインストール
- **依存関係**: 後続のコードデプロイで使用

#### 1.3.2 アプリケーション用ユーザー作成

**タスク3: Node.jsアプリケーション用ユーザー作成**
```yaml
- name: Node.jsアプリケーション用ユーザー作成
  user:
    name: "{{ app_user }}"
    system: yes
    shell: /bin/bash
    home: "{{ app_dir }}"
    create_home: yes
```
- **モジュール**: user
- **セキュリティ考慮**: システムユーザーとして作成
- **ホームディレクトリ**: アプリケーションディレクトリと同一
- **シェル**: /bin/bash（デバッグ時のアクセス用）

#### 1.3.3 Node.js環境構築

**タスク4: Node.js直接ダウンロード・インストール**
```yaml
- name: Node.js 16.x LTS直接ダウンロード・インストール
  shell: |
    cd /tmp
    curl -fsSL https://nodejs.org/dist/v16.20.2/node-v16.20.2-linux-x64.tar.xz -o node-v16.20.2-linux-x64.tar.xz
    tar -xf node-v16.20.2-linux-x64.tar.xz
    cp -r node-v16.20.2-linux-x64/* /usr/local/
    ln -sf /usr/local/bin/node /usr/bin/node
    ln -sf /usr/local/bin/npm /usr/bin/npm
  args:
    creates: /usr/bin/node
```
- **モジュール**: shell
- **インストール方式**: 直接ダウンロード（リポジトリ依存なし）
- **バージョン**: Node.js 16.20.2 LTS
- **冪等性**: creates条件で重複実行防止
- **シンボリックリンク**: システムパスに配置

**タスク5-7: Node.js/npmバージョン確認**
```yaml
- name: Node.jsインストール確認
  command: /usr/bin/node --version
  register: node_version_check

- name: npmインストール確認  
  command: /usr/bin/npm --version
  register: npm_version_check

- name: Node.jsバージョン表示
  debug:
    msg: "インストールされたNode.jsバージョン: {{ node_version.stdout }}"
```
- **目的**: インストール成功確認とバージョン情報表示
- **register**: 実行結果を変数に保存
- **debug**: バージョン情報をログ出力

#### 1.3.4 アプリケーションデプロイ

**タスク8: アプリケーションディレクトリ作成**
```yaml
- name: アプリケーションディレクトリ作成
  file:
    path: "{{ app_dir }}"
    state: directory
    owner: "{{ app_user }}"
    group: "{{ app_user }}"
    mode: '0755'
```
- **モジュール**: file
- **権限設定**: nodejs:nodejs所有、755権限
- **ディレクトリ**: /opt/hello-world-webapp

**タスク9-10: テンプレートファイル配置**
```yaml
- name: package.json作成
  template:
    src: package.json.j2
    dest: "{{ app_dir }}/package.json"
    owner: "{{ app_user }}"
    group: "{{ app_user }}"
    mode: '0644'

- name: app.js作成
  template:
    src: app.js.j2
    dest: "{{ app_dir }}/app.js"
    owner: "{{ app_user }}"
    group: "{{ app_user }}"
    mode: '0644'
```
- **モジュール**: template
- **テンプレート**: Jinja2形式（.j2拡張子）
- **権限**: 実行ファイルは644権限
- **所有者**: nodejsユーザー

**タスク11: npm依存関係インストール**
```yaml
- name: npm依存関係インストール
  npm:
    path: "{{ app_dir }}"
    state: present
  become_user: "{{ app_user }}"
```
- **モジュール**: npm
- **実行ユーザー**: nodejsユーザーで実行
- **処理内容**: package.jsonの依存関係をインストール

#### 1.3.5 systemdサービス設定

**タスク12: systemdサービスファイル作成**
```yaml
- name: systemdサービスファイル作成
  copy:
    content: |
      [Unit]
      Description=Hello World Node.js Application
      After=network.target

      [Service]
      Type=simple
      User={{ app_user }}
      WorkingDirectory={{ app_dir }}
      ExecStart=/usr/bin/node app.js
      Restart=always
      RestartSec=10
      Environment=NODE_ENV=production

      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/{{ app_name }}.service
    mode: '0644'
```

**systemdサービス設定詳細**:
- **Type**: simple（フォアグラウンド実行）
- **User**: nodejsユーザーで実行
- **WorkingDirectory**: アプリケーションディレクトリ
- **ExecStart**: Node.js実行コマンド
- **Restart**: always（異常終了時自動再起動）
- **RestartSec**: 再起動間隔10秒
- **Environment**: 本番環境設定

**タスク13-14: サービス有効化・起動**
```yaml
- name: systemdデーモンリロード
  systemd:
    daemon_reload: yes

- name: Node.jsアプリケーションサービス有効化・起動
  systemd:
    name: "{{ app_name }}"
    enabled: yes
    state: started
```
- **daemon_reload**: 新しいサービスファイルを認識
- **enabled**: システム起動時の自動起動設定
- **state: started**: サービス即座に起動

#### 1.3.6 Nginx設定

**タスク15: Nginxインストール**
```yaml
- name: Amazon Linux ExtrasでNginxインストール
  shell: amazon-linux-extras install nginx1 -y
  args:
    creates: /usr/sbin/nginx
```
- **インストール方式**: Amazon Linux Extras使用
- **冪等性**: creates条件で重複実行防止

**タスク16: Nginx設定ファイル作成**
```yaml
- name: Nginx設定ファイル作成（HTTP初期設定）
  copy:
    content: |
      server {
          listen 80;
          server_name {{ domain_name }} {{ ansible_default_ipv4.address }};
          
          # セキュリティヘッダー
          add_header X-Frame-Options DENY always;
          add_header X-Content-Type-Options nosniff always;
          add_header X-XSS-Protection "1; mode=block" always;
          
          # Let's Encrypt証明書検証用
          location /.well-known/acme-challenge/ {
              root /var/www/html;
          }
          
          # Node.jsアプリケーションへのリバースプロキシ
          location / {
              proxy_pass http://127.0.0.1:3000;
              proxy_http_version 1.1;
              proxy_set_header Upgrade $http_upgrade;
              proxy_set_header Connection 'upgrade';
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto $scheme;
              proxy_cache_bypass $http_upgrade;
          }
      }
    dest: /etc/nginx/conf.d/{{ app_name }}.conf
    backup: yes
```

**Nginx設定詳細**:
- **listen**: ポート80でHTTP接続受付
- **server_name**: IPアドレスとドメイン名対応
- **セキュリティヘッダー**: XSS、クリックジャッキング対策
- **Let's Encrypt対応**: ACME Challenge用パス設定
- **リバースプロキシ**: Node.jsアプリ（ポート3000）への転送
- **WebSocket対応**: Upgradeヘッダー処理
- **backup**: 既存設定ファイルのバックアップ作成

#### 1.3.7 SSL証明書準備

**タスク17-19: EPEL・Certbotインストール**
```yaml
- name: Amazon Linux ExtrasでEPELリポジトリ有効化
  shell: amazon-linux-extras install epel -y
  args:
    creates: /etc/yum.repos.d/epel.repo

- name: Certbotインストール
  yum:
    name: 
      - certbot
      - python2-certbot-nginx
    state: present
```
- **EPEL**: Extra Packages for Enterprise Linux
- **Certbot**: Let's Encrypt SSL証明書自動取得ツール
- **python2-certbot-nginx**: Nginx連携プラグイン

#### 1.3.8 ファイアウォール設定

**タスク20-25: firewalld設定**
```yaml
- name: firewalldインストール
  yum:
    name: firewalld
    state: present

- name: firewalldサービス確認・起動
  systemd:
    name: firewalld
    enabled: yes
    state: started

- name: HTTP許可（ファイアウォール）
  firewalld:
    service: http
    permanent: yes
    state: enabled
    immediate: yes

- name: HTTPS許可（ファイアウォール）
  firewalld:
    service: https
    permanent: yes
    state: enabled
    immediate: yes
```

**ファイアウォール設定詳細**:
- **firewalld**: CentOS/RHEL系標準ファイアウォール
- **HTTP/HTTPS**: ポート80/443の通信許可
- **permanent**: 再起動後も設定維持
- **immediate**: 即座に設定適用

#### 1.3.9 最終設定・確認

**タスク26-32: 最終設定と状態確認**
```yaml
- name: /var/www/htmlディレクトリ作成
  file:
    path: /var/www/html
    state: directory
    mode: '0755'

- name: デフォルトNginx設定無効化
  file:
    path: /etc/nginx/conf.d/default.conf
    state: absent

- name: Nginx設定テスト
  command: nginx -t
  register: nginx_test

- name: Nginx有効化・起動
  systemd:
    name: nginx
    enabled: yes
    state: started

- name: サービス状態確認
  systemd:
    name: "{{ app_name }}"
  register: app_service_status

- name: デプロイ完了メッセージ
  debug:
    msg: |
      🎉 Hello World Node.jsアプリケーションのデプロイが完了しました！
      📱 アクセス情報: http://{{ ansible_default_ipv4.address }}
```

### 1.4 実行要件

#### システム要件
- **OS**: Amazon Linux 2
- **メモリ**: 最小1GB（推奨2GB以上）
- **ディスク**: 最小5GB空き容量
- **ネットワーク**: インターネット接続必須

#### 前提条件
- **SSH接続**: 制御ノードからターゲットノードへのSSH接続
- **sudo権限**: ターゲットノードでのsudo実行権限
- **Python**: Python 2.7以上がインストール済み

#### 実行時間
- **初回実行**: 約15-25分
- **再実行**: 約5-10分（冪等性により短縮）

## 2. target_server_verification.yml 仕様

### 2.1 基本情報
- **ファイル名**: target_server_verification.yml
- **目的**: ターゲットサーバの基本情報収集と動作確認
- **対象ホスト**: target_servers
- **実行権限**: become: yes（sudo権限必要）
- **ファクト収集**: gather_facts: yes

### 2.2 タスク詳細仕様

#### 2.2.1 システム情報収集

**タスク1: システム情報収集**
```yaml
- name: システム情報収集
  debug:
    msg: |
      ホスト名: {{ ansible_hostname }}
      OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
      アーキテクチャ: {{ ansible_architecture }}
      IPアドレス: {{ ansible_default_ipv4.address }}
```
- **モジュール**: debug
- **収集情報**: ホスト名、OS、アーキテクチャ、IPアドレス
- **データソース**: Ansibleファクト（gather_facts）

#### 2.2.2 リソース状態確認

**タスク2-3: ディスク使用量確認**
```yaml
- name: ディスク使用量確認
  command: df -h
  register: disk_usage

- name: ディスク使用量表示
  debug:
    var: disk_usage.stdout_lines
```
- **コマンド**: df -h（人間が読みやすい形式）
- **register**: 実行結果を変数に保存
- **表示**: 標準出力を行単位で表示

**タスク4-5: メモリ情報確認**
```yaml
- name: メモリ情報確認
  command: free -h
  register: memory_info

- name: メモリ情報表示
  debug:
    var: memory_info.stdout_lines
```
- **コマンド**: free -h（人間が読みやすい形式）
- **情報**: 総メモリ、使用量、空き容量、スワップ

**タスク6-7: 稼働時間確認**
```yaml
- name: 稼働時間確認
  command: uptime
  register: uptime_info

- name: 稼働時間表示
  debug:
    var: uptime_info.stdout
```
- **コマンド**: uptime
- **情報**: システム稼働時間、ロードアベレージ

#### 2.2.3 テストファイル操作

**タスク8: テストディレクトリ作成**
```yaml
- name: テストディレクトリ作成
  file:
    path: /tmp/ansible_test
    state: directory
    mode: '0755'
```
- **モジュール**: file
- **パス**: /tmp/ansible_test
- **権限**: 755（読み書き実行可能）

**タスク9: テストファイル作成**
```yaml
- name: テストファイル作成
  copy:
    content: |
      Ansibleによるターゲットサーバ管理テスト
      作成日時: {{ ansible_date_time.iso8601 }}
      制御ノード: oshima_yoshie_devin_ec2
      ターゲットノード: {{ ansible_hostname }}
    dest: /tmp/ansible_test/verification.txt
    mode: '0644'
```
- **モジュール**: copy
- **内容**: テスト情報とタイムスタンプ
- **動的情報**: 作成日時、ホスト名を自動挿入

**タスク10-11: ファイル内容確認**
```yaml
- name: 作成ファイル確認
  command: cat /tmp/ansible_test/verification.txt
  register: test_file_content

- name: ファイル内容表示
  debug:
    var: test_file_content.stdout_lines
```
- **コマンド**: cat（ファイル内容表示）
- **確認**: 作成したファイルの内容を検証

#### 2.2.4 パッケージ・サービス情報

**タスク12-13: パッケージ情報確認**
```yaml
- name: パッケージ情報確認（yum）
  yum:
    list: installed
  register: installed_packages

- name: インストール済みパッケージ数表示
  debug:
    msg: "インストール済みパッケージ数: {{ installed_packages.results | length }}"
```
- **モジュール**: yum
- **処理**: インストール済みパッケージ一覧取得
- **表示**: パッケージ総数

**タスク14-15: サービス状態確認**
```yaml
- name: サービス状態確認
  service_facts:

- name: 実行中サービス数表示
  debug:
    msg: "サービス情報収集完了: {{ ansible_facts.services.keys() | list | length }} 個のサービスを確認"
```
- **モジュール**: service_facts
- **処理**: 全サービス状態収集
- **表示**: サービス総数

### 2.3 実行要件

#### システム要件
- **OS**: Amazon Linux 2 / CentOS / RHEL
- **メモリ**: 最小512MB
- **ディスク**: 最小1GB空き容量

#### 実行時間
- **通常実行**: 約2-5分
- **初回実行**: 約3-7分（パッケージ情報収集時間含む）

### 2.4 出力例

#### システム情報出力例
```
ホスト名: ip-172-31-32-123
OS: Amazon Linux 2
アーキテクチャ: x86_64
IPアドレス: 172.31.32.123
```

#### リソース情報出力例
```
ディスク使用量:
Filesystem      Size  Used Avail Use% Mounted on
/dev/xvda1       8.0G  1.5G  6.5G  19% /

メモリ情報:
              total        used        free      shared  buff/cache   available
Mem:           1.0G        200M        600M        1.0M        200M        700M
```

## 3. ansible_inventory.ini 仕様

### 3.1 基本構成
```ini
[target_servers]
oshima_yoshie_devin_target_ec2 ansible_host=13.230.71.11 ansible_user=ec2-user ansible_ssh_private_key_file=/home/ec2-user/oshima_devin.pem

[target_servers:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_python_interpreter=/usr/bin/python
```

### 3.2 設定詳細

#### 3.2.1 ホスト定義
- **ホスト名**: oshima_yoshie_devin_target_ec2
- **IPアドレス**: 13.230.71.11
- **接続ユーザー**: ec2-user
- **認証方式**: SSH秘密鍵認証

#### 3.2.2 SSH設定
- **秘密鍵ファイル**: /home/ec2-user/oshima_devin.pem
- **ホスト鍵確認**: 無効化（StrictHostKeyChecking=no）
- **Python実行環境**: /usr/bin/python

#### 3.2.3 セキュリティ考慮事項
- **秘密鍵権限**: 600（所有者のみ読み書き可能）
- **接続暗号化**: SSH暗号化通信
- **認証強度**: 公開鍵認証使用

## 4. テンプレートファイル仕様

### 4.1 package.json.j2
```json
{
  "name": "hello-world-webapp",
  "version": "1.0.0",
  "description": "Node.jsで作成したHello Worldウェブアプリケーション",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "dev": "node app.js"
  },
  "dependencies": {
    "express": "^4.21.2"
  },
  "keywords": [
    "nodejs",
    "express",
    "hello-world",
    "webapp"
  ],
  "author": "oshima.yoshie@ditgroup.jp",
  "license": "MIT"
}
```

### 4.2 app.js.j2
- **テンプレート変数**: ポート番号、作成者情報
- **動的コンテンツ**: 実行時情報の挿入
- **スタイル**: CSS埋め込み型レスポンシブデザイン

## 5. 実行手順

### 5.1 事前準備
1. **制御ノード準備**
   - Ansibleインストール
   - SSH秘密鍵配置
   - インベントリファイル設定

2. **ターゲットノード準備**
   - EC2インスタンス起動
   - セキュリティグループ設定（HTTP/HTTPS許可）
   - SSH接続確認

### 5.2 実行コマンド

#### Webサーバセットアップ実行
```bash
ansible-playbook -i ansible_inventory.ini web_server_setup.yml -v
```

#### サーバ検証実行
```bash
ansible-playbook -i ansible_inventory.ini target_server_verification.yml -v
```

### 5.3 実行結果確認

#### 成功確認項目
- **Node.jsサービス**: systemctl status hello-world-webapp
- **Nginxサービス**: systemctl status nginx
- **ポート確認**: netstat -tlnp | grep :80
- **アプリケーション確認**: curl http://サーバIP

#### ログ確認
- **systemdログ**: journalctl -u hello-world-webapp
- **Nginxログ**: tail -f /var/log/nginx/access.log
- **アプリケーションログ**: Node.jsコンソール出力

## 6. トラブルシューティング

### 6.1 よくある問題

#### SSH接続エラー
```
UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh"}
```
**解決方法**:
- 秘密鍵ファイルの権限確認（600）
- セキュリティグループでSSH（22番ポート）許可
- IPアドレス・ユーザー名確認

#### Node.jsインストールエラー
```
FAILED! => {"changed": false, "msg": "No package nodejs available"}
```
**解決方法**:
- インターネット接続確認
- 直接ダウンロード方式使用（プレイブック内で実装済み）

#### サービス起動エラー
```
Job for hello-world-webapp.service failed
```
**解決方法**:
- journalctl -u hello-world-webapp でログ確認
- Node.jsバイナリパス確認
- アプリケーションファイル権限確認

### 6.2 デバッグ手順

1. **詳細ログ出力**: -vvv オプション使用
2. **ステップ実行**: --step オプション使用
3. **特定タスク実行**: --tags オプション使用
4. **構文チェック**: --syntax-check オプション使用

この仕様書により、Ansibleプレイブックの詳細な動作と設定が理解できます。
