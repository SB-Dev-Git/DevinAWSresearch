#!/bin/bash

echo "=== EC2インスタンス起動スクリプト ==="
echo ""

echo "制御ノード (oshima_yoshie_devin_ec2) を起動中..."
aws ec2 start-instances --instance-ids i-0d1c0d59300c93fb9

echo "ターゲットノード (oshima_yoshie_devin_target_ec2) を起動中..."
aws ec2 start-instances --instance-ids i-00684986b921d00fa

echo ""
echo "インスタンス起動完了を待機中..."
aws ec2 wait instance-running --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa

echo ""
echo "=== インスタンス情報 ==="
aws ec2 describe-instances --instance-ids i-0d1c0d59300c93fb9 i-00684986b921d00fa --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,PublicIP:PublicIpAddress,Name:Tags[?Key==`Name`].Value|[0]}' --output table

echo ""
echo "✅ EC2インスタンス起動完了！"
echo "📝 次のステップ: ./deploy_hello_world.sh を実行してください"
