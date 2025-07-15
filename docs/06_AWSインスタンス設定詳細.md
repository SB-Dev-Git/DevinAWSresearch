# AWSインスタンス設定詳細ドキュメント

## 概要

このドキュメントでは、DevinAWSresearchシステムで使用されるAWSインスタンスの詳細設定と、動的IPアドレス変化への対応状況について説明します。

## 1. AWSインスタンス構成

### 1.1 システム構成概要

DevinAWSresearchシステムは以下の2つのEC2インスタンスで構成されています：

| 役割 | インスタンス名 | インスタンスID | 用途 |
|------|---------------|----------------|------|
| 制御ノード | oshima_yoshie_devin_ec2 | i-0d1c0d59300c93fb9 | Ansible制御、AWS検証スクリプト実行 |
| ターゲットノード | oshima_yoshie_devin_target_ec2 | i-00684986b921d00fa | Node.jsアプリケーション、Webサーバ |

### 1.2 制御ノード詳細設定

**インスタンス基本情報**:
- **インスタンスID**: `i-0d1c0d59300c93fb9`
- **インスタンス名**: `oshima_yoshie_devin_ec2`
- **役割**: Ansible制御ノード、AWS検証システム実行環境

**推奨仕様**:
- **インスタンスタイプ**: t3.micro以上（AWS検証処理に十分なCPU/メモリ）
- **OS**: Amazon Linux 2
- **ストレージ**: 20GB以上（ログファイル、一時ファイル用）

**必要なソフトウェア**:
- Python 3.8以上
- boto3ライブラリ
- AWS CLI
- Ansible 2.9以上
- SSH クライアント

**セキュリティグループ設定**:
```
アウトバウンド:
- HTTPS (443): 0.0.0.0/0 (AWS API通信用)
- HTTP (80): 0.0.0.0/0 (パッケージダウンロード用)
- SSH (22): ターゲットノードIP (Ansible接続用)

インバウンド:
- SSH (22): 管理者IPアドレス範囲
```

### 1.3 ターゲットノード詳細設定

**インスタンス基本情報**:
- **インスタンスID**: `i-00684986b921d00fa`
- **インスタンス名**: `oshima_yoshie_devin_target_ec2`
- **役割**: Node.jsアプリケーション実行環境

**推奨仕様**:
- **インスタンスタイプ**: t3.micro以上（Node.jsアプリケーション実行用）
- **OS**: Amazon Linux 2
- **ストレージ**: 20GB以上（アプリケーション、ログ用）

**必要なソフトウェア**:
- Node.js 18.x LTS
- npm
- Nginx
- systemd
- firewalld

**セキュリティグループ設定**:
```
アウトバウンド:
- HTTPS (443): 0.0.0.0/0 (パッケージダウンロード用)
- HTTP (80): 0.0.0.0/0 (パッケージダウンロード用)

インバウンド:
- SSH (22): 制御ノードIP
- HTTP (80): 0.0.0.0/0 (Webアプリケーションアクセス用)
- HTTPS (443): 0.0.0.0/0 (SSL対応時)
```

## 2. 動的IPアドレス対応状況分析

### 2.1 現在の対応状況概要

EC2インスタンスは起動するたびにパブリックIPv4アドレスが変化するため、システム全体での動的IP対応が重要です。

**対応状況サマリー**:
- ✅ **完全対応**: 2ファイル
- ❌ **要改善**: 3ファイル + ドキュメント

### 2.2 ファイル別対応状況詳細

#### 2.2.1 ✅ 動的IP対応済みファイル

**1. deploy_hello_world.sh**
```bash
# 動的IP取得の実装例
CONTROL_IP=$(aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
TARGET_IP=$(aws ec2 describe-instances --instance-ids i-00684986b921d00fa --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
```

**対応内容**:
- AWS CLIを使用してリアルタイムでIPアドレスを取得
- 取得したIPアドレスを変数に格納して使用
- インスタンス停止時の適切なエラーハンドリング

**2. start_instances.sh**
```bash
# インスタンス情報の動的表示
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,PublicIP:PublicIpAddress,Name:Tags[?Key==`Name`].Value|[0]}' --output table
```

**対応内容**:
- インスタンス起動後の現在のIPアドレスを動的に表示
- 起動状態とIPアドレスの確認が可能

#### 2.2.2 ❌ 動的IP対応が必要なファイル

**1. run_ansible_verification.sh**

**現在の問題**:
```bash
# ハードコードされたIPアドレス
ssh -i oshima_devin.pem -o StrictHostKeyChecking=no ec2-user@13.231.135.17 << 'EOF'
```

**推奨改善案**:
```bash
#!/bin/bash

echo "=== Ansibleターゲットサーバ検証開始 ==="

# 動的IP取得
CONTROL_IP=$(aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
TARGET_IP=$(aws ec2 describe-instances --instance-ids i-00684986b921d00fa --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "制御ノード: oshima_yoshie_devin_ec2 ($CONTROL_IP)"
echo "ターゲットノード: oshima_yoshie_devin_target_ec2 ($TARGET_IP)"
echo ""

# インスタンス状態確認
if [ "$CONTROL_IP" = "None" ] || [ "$TARGET_IP" = "None" ]; then
    echo "⚠️  EC2インスタンスが停止しています。先にインスタンスを起動してください。"
    exit 1
fi

ssh -i oshima_devin.pem -o StrictHostKeyChecking=no ec2-user@$CONTROL_IP << EOF
cd /tmp
echo "=== インベントリファイル作成 ==="
cat > ansible_inventory.ini << 'INVENTORY'
[target_servers]
oshima_yoshie_devin_target_ec2 ansible_host=$TARGET_IP ansible_user=ec2-user ansible_ssh_private_key_file=/home/ec2-user/oshima_devin.pem

[target_servers:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_python_interpreter=/usr/bin/python
INVENTORY

echo "=== プレイブック実行 ==="
ansible-playbook -i ansible_inventory.ini /tmp/target_verification.yml -v
EOF
```

**2. ansible_inventory.ini**

**現在の問題**:
```ini
[target_servers]
oshima_yoshie_devin_target_ec2 ansible_host=13.230.71.11 ansible_user=ec2-user ansible_ssh_private_key_file=/home/ec2-user/oshima_devin.pem
```

**推奨改善案**:
- 静的ファイルではなく、実行時に動的生成する方式に変更
- `deploy_hello_world.sh`で実装されているような動的インベントリ生成を他のスクリプトでも採用

**3. ドキュメント内のハードコードされたIP参照**

**影響範囲**:
- `docs/02_構成図.md`: 制御ノード (13.231.135.17)、ターゲットノード (13.230.71.11)
- `docs/04_Ansibleプレイブック仕様書.md`: ターゲットノード (13.230.71.11)
- `docs/05_インフラ構成管理ドキュメント.md`: 両ノードのIP参照
- `README_DEPLOYMENT.md`: 両ノードのIP参照

**推奨改善案**:
- ドキュメント内では具体的なIPアドレスではなく、変数表記を使用
- 例: `<CONTROL_NODE_IP>`、`<TARGET_NODE_IP>`
- 実際のIPアドレスは実行時に動的に取得する旨を明記

## 3. AWS CLI コマンドリファレンス

### 3.1 インスタンス情報取得

**基本的なインスタンス情報取得**:
```bash
# 両インスタンスの基本情報
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa

# IPアドレスのみ取得
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

# 詳細情報をテーブル形式で表示
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,PublicIP:PublicIpAddress,PrivateIP:PrivateIpAddress,InstanceType:InstanceType,Name:Tags[?Key==`Name`].Value|[0]}' --output table
```

**インスタンス制御**:
```bash
# インスタンス起動
aws ec2 start-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa

# インスタンス停止
aws ec2 stop-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa

# 起動完了待機
aws ec2 wait instance-running --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa

# 停止完了待機
aws ec2 wait instance-stopped --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa
```

### 3.2 セキュリティグループ情報取得

```bash
# インスタンスのセキュリティグループ取得
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].SecurityGroups[].GroupId' --output text

# セキュリティグループの詳細情報
aws ec2 describe-security-groups --group-ids <SECURITY_GROUP_ID>
```

### 3.3 ネットワーク情報取得

```bash
# VPC情報取得
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].VpcId' --output text

# サブネット情報取得
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].SubnetId' --output text
```

## 4. 動的IP対応のベストプラクティス

### 4.1 推奨実装パターン

**1. 実行時IP取得パターン**:
```bash
# 関数として定義
get_instance_ip() {
    local instance_id=$1
    aws ec2 describe-instances --instance-ids $instance_id --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
}

# 使用例
CONTROL_IP=$(get_instance_ip i-0d1c0d59300c93fb9)
TARGET_IP=$(get_instance_ip i-00684986b921d00fa)
```

**2. エラーハンドリング付きパターン**:
```bash
get_instance_ip_safe() {
    local instance_id=$1
    local ip=$(aws ec2 describe-instances --instance-ids $instance_id --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>/dev/null)
    
    if [ "$ip" = "None" ] || [ -z "$ip" ]; then
        echo "ERROR: インスタンス $instance_id のIPアドレスを取得できません" >&2
        return 1
    fi
    
    echo $ip
}
```

**3. 設定ファイル動的生成パターン**:
```bash
# Ansibleインベントリの動的生成
generate_ansible_inventory() {
    local target_ip=$1
    cat > ansible_inventory.ini << EOF
[target_servers]
oshima_yoshie_devin_target_ec2 ansible_host=$target_ip ansible_user=ec2-user ansible_ssh_private_key_file=/home/ec2-user/oshima_devin.pem

[target_servers:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_python_interpreter=/usr/bin/python
EOF
}
```

### 4.2 Python スクリプトでの動的IP対応

**boto3を使用したIP取得**:
```python
import boto3

def get_instance_public_ip(instance_id):
    """EC2インスタンスのパブリックIPアドレスを取得"""
    ec2_client = boto3.client('ec2')
    
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        return instance.get('PublicIpAddress')
    except Exception as e:
        print(f"エラー: インスタンス {instance_id} のIP取得に失敗: {e}")
        return None

# 使用例
control_ip = get_instance_public_ip('i-0d1c0d59300c93fb9')
target_ip = get_instance_public_ip('i-00684986b921d00fa')
```

## 5. トラブルシューティング

### 5.1 よくある問題と解決方法

**問題1: IPアドレスが取得できない**
```bash
# 症状: aws ec2 describe-instances でIPが "None" になる
# 原因: インスタンスが停止している、またはパブリックIPが割り当てられていない

# 解決方法:
# 1. インスタンス状態確認
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].State.Name' --output text

# 2. インスタンス起動
aws ec2 start-instances --instance-ids i-0d1c0d59300c93fb9

# 3. 起動完了待機
aws ec2 wait instance-running --instance-ids i-0d1c0d59300c93fb9
```

**問題2: SSH接続が失敗する**
```bash
# 症状: ssh接続時に "Connection refused" または "Host unreachable"
# 原因: IPアドレスが古い、セキュリティグループ設定、インスタンス未起動

# 解決方法:
# 1. 最新IPアドレス確認
CURRENT_IP=$(aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "現在のIP: $CURRENT_IP"

# 2. セキュリティグループ確認
aws ec2 describe-security-groups --group-ids <SECURITY_GROUP_ID>

# 3. SSH接続テスト
ssh -i oshima_devin.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@$CURRENT_IP echo "接続成功"
```

**問題3: Ansible接続エラー**
```bash
# 症状: ansible-playbook実行時に接続エラー
# 原因: インベントリファイルのIPアドレスが古い

# 解決方法:
# 1. 動的インベントリ生成
TARGET_IP=$(aws ec2 describe-instances --instance-ids i-00684986b921d00fa --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# 2. インベントリファイル更新
cat > ansible_inventory.ini << EOF
[target_servers]
oshima_yoshie_devin_target_ec2 ansible_host=$TARGET_IP ansible_user=ec2-user ansible_ssh_private_key_file=/home/ec2-user/oshima_devin.pem

[target_servers:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_python_interpreter=/usr/bin/python
EOF

# 3. 接続テスト
ansible target_servers -i ansible_inventory.ini -m ping
```

### 5.2 監視とログ

**インスタンス状態監視**:
```bash
# 定期的なインスタンス状態確認スクリプト
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,PublicIP:PublicIpAddress}' --output table
    sleep 300  # 5分間隔
done
```

**ログファイル場所**:
- AWS CLI ログ: `~/.aws/cli/cache/`
- システムログ: `/var/log/messages`
- SSH接続ログ: `/var/log/secure`

## 6. セキュリティ考慮事項

### 6.1 動的IP環境でのセキュリティ

**推奨設定**:
- セキュリティグループでの適切なポート制限
- SSH鍵認証の使用（パスワード認証無効化）
- 定期的なセキュリティグループルールの見直し
- CloudTrailによるAPI呼び出しログの監視

**注意事項**:
- パブリックIPアドレスは外部からアクセス可能
- 不要なポートは必ず閉じる
- SSH接続は信頼できるIPアドレスからのみ許可

### 6.2 アクセス制御

**IAM権限設定**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:StartInstances",
                "ec2:StopInstances"
            ],
            "Resource": [
                "arn:aws:ec2:*:*:instance/i-0d1c0d59300c93fb9",
                "arn:aws:ec2:*:*:instance/i-00684986b921d00fa"
            ]
        }
    ]
}
```

## 7. パフォーマンス最適化

### 7.1 IP取得の最適化

**キャッシュ機能付きIP取得**:
```bash
# IP取得結果をキャッシュして高速化
CACHE_FILE="/tmp/instance_ips.cache"
CACHE_DURATION=300  # 5分

get_cached_ip() {
    local instance_id=$1
    local cache_key="ip_${instance_id}"
    
    if [ -f "$CACHE_FILE" ]; then
        local cached_time=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)
        local current_time=$(date +%s)
        
        if [ $((current_time - cached_time)) -lt $CACHE_DURATION ]; then
            grep "^${cache_key}=" "$CACHE_FILE" | cut -d'=' -f2
            return 0
        fi
    fi
    
    # キャッシュが無効な場合は新しく取得
    local ip=$(aws ec2 describe-instances --instance-ids $instance_id --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    echo "${cache_key}=${ip}" >> "$CACHE_FILE"
    echo $ip
}
```

### 7.2 並列処理による高速化

```bash
# 複数インスタンスのIP取得を並列実行
get_all_ips_parallel() {
    {
        CONTROL_IP=$(aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text) &
        TARGET_IP=$(aws ec2 describe-instances --instance-ids i-00684986b921d00fa --query 'Reservations[0].Instances[0].PublicIpAddress' --output text) &
        wait
    }
    
    echo "制御ノードIP: $CONTROL_IP"
    echo "ターゲットノードIP: $TARGET_IP"
}
```

## 8. 今後の改善提案

### 8.1 短期的改善項目

1. **run_ansible_verification.sh の動的IP対応**
   - 優先度: 高
   - 工数: 1-2時間
   - 効果: インスタンス再起動時の自動対応

2. **ドキュメント内IP参照の変数化**
   - 優先度: 中
   - 工数: 2-3時間
   - 効果: ドキュメントの保守性向上

3. **エラーハンドリングの強化**
   - 優先度: 中
   - 工数: 2-3時間
   - 効果: 運用時のトラブル削減

### 8.2 長期的改善項目

1. **Elastic IP の導入検討**
   - 固定IPアドレスによる根本的解決
   - コスト増加とのトレードオフ検討が必要

2. **Route 53 による DNS 管理**
   - ドメイン名による接続で IP 変化を隠蔽
   - SSL証明書管理の簡素化

3. **Infrastructure as Code (Terraform) 導入**
   - インフラ構成の自動化とバージョン管理
   - 環境の再現性向上

## 9. 関連ドキュメント

- [リソース一覧](./01_リソース一覧.md) - システム全体のリソース概要
- [構成図](./02_構成図.md) - システムアーキテクチャ図解
- [処理設計書](./03_処理設計書.md) - 各処理の詳細仕様
- [Ansibleプレイブック仕様書](./04_Ansibleプレイブック仕様書.md) - Ansible設定詳細
- [インフラ構成管理ドキュメント](./05_インフラ構成管理ドキュメント.md) - インフラ管理手順

## 10. 更新履歴

- 2025-07-15: 初版作成
  - AWSインスタンス設定詳細の文書化
  - 動的IPアドレス対応状況の分析
  - 改善提案とベストプラクティスの追加

---

**📋 このドキュメントは DevinAWSresearch システムの AWS インスタンス設定と動的IP対応の包括的なガイドです**
