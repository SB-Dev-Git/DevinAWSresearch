#!/bin/bash

echo "=== Ansibleターゲットサーバ検証開始 ==="

echo "=== EC2インスタンス状態確認 ==="
CONTROL_IP=$(aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
TARGET_IP=$(aws ec2 describe-instances --instance-ids i-00684986b921d00fa --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "制御ノード: oshima_yoshie_devin_ec2 ($CONTROL_IP)"
echo "ターゲットノード: oshima_yoshie_devin_target_ec2 ($TARGET_IP)"
echo ""

if [ "$CONTROL_IP" = "None" ] || [ "$TARGET_IP" = "None" ]; then
    echo "⚠️  EC2インスタンスが停止しています。先にインスタンスを起動してください。"
    echo "aws ec2 start-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa"
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
