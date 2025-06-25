#!/bin/bash

echo "=== Hello World Node.jsアプリケーション自動デプロイ ==="
echo "制御ノード: oshima_yoshie_devin_ec2"
echo "ターゲットノード: oshima_yoshie_devin_target_ec2"
echo ""

echo "=== EC2インスタンス状態確認 ==="
CONTROL_IP=$(aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
TARGET_IP=$(aws ec2 describe-instances --instance-ids i-00684986b921d00fa --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "制御ノードIP: $CONTROL_IP"
echo "ターゲットノードIP: $TARGET_IP"
echo ""

if [ "$CONTROL_IP" = "None" ] || [ "$TARGET_IP" = "None" ]; then
    echo "⚠️  EC2インスタンスが停止しています。先にインスタンスを起動してください。"
    echo "aws ec2 start-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa"
    exit 1
fi

echo "=== ファイル転送 ==="
scp -i oshima_devin.pem -o StrictHostKeyChecking=no web_server_setup.yml ec2-user@$CONTROL_IP:/tmp/
scp -i oshima_devin.pem -o StrictHostKeyChecking=no ansible_inventory.ini ec2-user@$CONTROL_IP:/tmp/

ssh -i oshima_devin.pem -o StrictHostKeyChecking=no ec2-user@$CONTROL_IP << EOF
sed -i "s/ansible_host=.*/ansible_host=$TARGET_IP/" /tmp/ansible_inventory.ini
EOF

echo "=== Webサーバセットアッププレイブック実行 ==="
ssh -i oshima_devin.pem -o StrictHostKeyChecking=no ec2-user@$CONTROL_IP << 'EOF'
cd /tmp

echo "=== Ansibleプレイブック構文チェック ==="
ansible-playbook --syntax-check -i ansible_inventory.ini web_server_setup.yml

if [ $? -eq 0 ]; then
    echo "✅ プレイブック構文チェック成功"
    echo ""
    echo "=== プレイブック実行開始 ==="
    ansible-playbook -i ansible_inventory.ini web_server_setup.yml -v
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 デプロイ完了！"
        echo "📱 HTTPアクセス: http://$TARGET_IP"
        echo "🔒 HTTPS設定は実際のドメイン名で手動完了してください"
        echo ""
        echo "=== サービス状態確認 ==="
        ansible target_servers -i ansible_inventory.ini -m shell -a "systemctl status hello-world-webapp --no-pager"
        ansible target_servers -i ansible_inventory.ini -m shell -a "systemctl status nginx --no-pager"
    else
        echo "❌ プレイブック実行に失敗しました"
        exit 1
    fi
else
    echo "❌ プレイブック構文エラーがあります"
    exit 1
fi
EOF
