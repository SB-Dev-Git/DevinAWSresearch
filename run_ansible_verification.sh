#!/bin/bash

echo "=== Ansibleターゲットサーバ検証開始 ==="
echo "制御ノード: oshima_yoshie_devin_ec2 (13.231.135.17)"
echo "ターゲットノード: oshima_yoshie_devin_target_ec2 (13.230.71.11)"
echo ""

ssh -i oshima_devin.pem -o StrictHostKeyChecking=no ec2-user@13.231.135.17 << 'EOF'
cd /tmp
echo "=== インベントリファイル作成 ==="
cat > ansible_inventory.ini << 'INVENTORY'
[target_servers]
oshima_yoshie_devin_target_ec2 ansible_host=13.230.71.11 ansible_user=ec2-user ansible_ssh_private_key_file=/home/ec2-user/oshima_devin.pem

[target_servers:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_python_interpreter=/usr/bin/python
INVENTORY

echo "=== プレイブック実行 ==="
ansible-playbook -i ansible_inventory.ini /tmp/target_verification.yml -v
EOF
