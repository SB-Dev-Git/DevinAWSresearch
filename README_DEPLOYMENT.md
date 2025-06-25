# Hello World Node.js アプリケーション自動デプロイシステム

## 概要

このシステムは、Ansibleを使用してHello World Node.jsアプリケーションを自動デプロイし、包括的なWebサーバ環境を構築します。

## システム構成

### サーバ構成
- **制御ノード**: oshima_yoshie_devin_ec2 (13.231.135.17)
- **ターゲットノード**: oshima_yoshie_devin_target_ec2 (13.230.71.11)

### 実装機能

#### ✅ 自動インストール・設定
- **Git**: バージョン管理とコードデプロイ
- **Node.js 18.x**: 最新LTS版のランタイム環境
- **npm**: パッケージ管理
- **Express.js**: Webアプリケーションフレームワーク

#### ✅ アプリケーション管理
- **systemdサービス化**: 自動起動・プロセス管理
- **専用ユーザー**: セキュリティ向上のための分離実行
- **プロセス監視**: 自動再起動機能

#### ✅ Webサーバ設定
- **Nginx**: 高性能リバースプロキシサーバ
- **リバースプロキシ**: Node.jsアプリへの転送設定
- **セキュリティヘッダー**: XSS、CSRF対策

#### ✅ セキュリティ設定
- **ファイアウォール**: HTTP/HTTPS通信許可
- **SSL/TLS対応**: Let's Encrypt証明書サポート
- **HTTPSリダイレクト**: 自動暗号化通信

## ファイル構成

```
DevinAWSresearch/
├── web_server_setup.yml          # メインのAnsibleプレイブック
├── deploy_hello_world.sh         # デプロイ実行スクリプト
├── start_instances.sh            # EC2インスタンス起動スクリプト
├── ansible_inventory.ini         # サーバ接続設定
├── app.js                        # Hello World Node.jsアプリケーション
├── package.json                  # Node.js依存関係設定
└── README_DEPLOYMENT.md          # このドキュメント
```

## 使用方法

### 1. EC2インスタンス起動

```bash
cd /home/ubuntu/repos/DevinAWSresearch
chmod +x start_instances.sh
./start_instances.sh
```

### 2. 自動デプロイ実行

```bash
chmod +x deploy_hello_world.sh
./deploy_hello_world.sh
```

### 3. 手動プレイブック実行（オプション）

```bash
# 制御ノードにSSH接続（IPアドレスは動的に変わります）
ssh -i oshima_devin.pem ec2-user@<CONTROL_NODE_IP>

# プレイブック実行
ansible-playbook -i ansible_inventory.ini web_server_setup.yml -v
```

## アクセス方法

### HTTP接続
```
http://<TARGET_SERVER_IP>
```
デプロイ完了後、スクリプトが実際のIPアドレスを表示します。

### HTTPS接続（SSL証明書設定後）
```
https://your-domain.com
```

## SSL証明書設定（手動）

Let's Encrypt証明書を取得するには、実際のドメイン名が必要です：

```bash
# ターゲットサーバにSSH接続（IPアドレスは動的に変わります）
ssh -i oshima_devin.pem ec2-user@<TARGET_SERVER_IP>

# SSL証明書取得
sudo certbot --nginx -d your-domain.com

# 自動更新設定
sudo crontab -e
# 以下を追加:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## サービス管理

### Node.jsアプリケーション
```bash
# サービス状態確認
sudo systemctl status hello-world-webapp

# サービス再起動
sudo systemctl restart hello-world-webapp

# ログ確認
sudo journalctl -u hello-world-webapp -f
```

### Nginx
```bash
# 設定テスト
sudo nginx -t

# サービス再起動
sudo systemctl restart nginx

# ログ確認
sudo tail -f /var/log/nginx/access.log
```

## トラブルシューティング

### よくある問題

#### 1. Node.jsアプリが起動しない
```bash
# ログ確認
sudo journalctl -u hello-world-webapp -n 50

# 手動起動テスト
sudo -u nodejs /usr/bin/node /opt/hello-world-webapp/app.js
```

#### 2. Nginxが起動しない
```bash
# 設定ファイル確認
sudo nginx -t

# エラーログ確認
sudo tail -f /var/log/nginx/error.log
```

#### 3. ファイアウォールでアクセスできない
```bash
# ファイアウォール状態確認
sudo firewall-cmd --list-all

# ポート開放確認
sudo firewall-cmd --list-ports
```

## セキュリティ考慮事項

### 実装済みセキュリティ機能
- ✅ 専用ユーザーでのアプリケーション実行
- ✅ ファイアウォール設定（HTTP/HTTPS のみ許可）
- ✅ Nginxセキュリティヘッダー設定
- ✅ SSL/TLS暗号化対応

### 追加推奨設定
- 🔄 定期的なシステムアップデート
- 🔄 ログ監視・ローテーション設定
- 🔄 侵入検知システム（IDS）導入
- 🔄 バックアップ戦略の実装

## パフォーマンス最適化

### 実装済み最適化
- ✅ Nginx HTTP/2対応
- ✅ SSL セッションキャッシュ
- ✅ Gzip圧縮（Nginx標準）

### 追加最適化案
- 🔄 CDN導入
- 🔄 データベース接続プール
- 🔄 Redis/Memcachedキャッシュ
- 🔄 ロードバランサー設定

## 監視・ログ

### ログファイル場所
```
/var/log/nginx/access.log          # Nginxアクセスログ
/var/log/nginx/error.log           # Nginxエラーログ
journalctl -u hello-world-webapp   # Node.jsアプリログ
/var/log/messages                  # システムログ
```

### 監視コマンド
```bash
# リアルタイムアクセス監視
sudo tail -f /var/log/nginx/access.log

# システムリソース監視
htop

# ネットワーク接続確認
sudo netstat -tlnp | grep -E '(80|443|3000)'
```

## 開発・デバッグ

### 開発モード起動
```bash
# Node.jsアプリを開発モードで起動
cd /opt/hello-world-webapp
sudo -u nodejs NODE_ENV=development node app.js
```

### 設定ファイル編集
```bash
# Nginx設定編集
sudo vi /etc/nginx/conf.d/hello-world-webapp.conf

# systemd設定編集
sudo vi /etc/systemd/system/hello-world-webapp.service
sudo systemctl daemon-reload
```

## バックアップ・復旧

### 重要ファイルのバックアップ
```bash
# アプリケーションコード
tar -czf hello-world-app-backup.tar.gz /opt/hello-world-webapp/

# Nginx設定
cp /etc/nginx/conf.d/hello-world-webapp.conf ~/nginx-backup.conf

# SSL証明書（取得後）
tar -czf ssl-backup.tar.gz /etc/letsencrypt/
```

## 技術仕様

### システム要件
- **OS**: Amazon Linux 2
- **RAM**: 最小 1GB（推奨 2GB以上）
- **ディスク**: 最小 10GB（推奨 20GB以上）
- **ネットワーク**: HTTP(80), HTTPS(443) ポート開放

### ソフトウェアバージョン
- **Node.js**: 18.x LTS
- **npm**: 最新版（Node.jsに付属）
- **Nginx**: 最新安定版
- **Ansible**: 2.9.27（制御ノード）

## サポート・問い合わせ

### 作成者
- **Email**: oshima.yoshie@ditgroup.jp
- **プロジェクト**: DevinAWSresearch

### ドキュメント更新履歴
- 2025-06-25: 初版作成
- システム構成・使用方法・トラブルシューティング情報を含む包括的なドキュメント

---

**🎉 Hello World Node.jsアプリケーションの自動デプロイシステムをお楽しみください！**
