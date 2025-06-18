#!/usr/bin/env python3
"""
ステップ2（中）: サービス接続テスト
S3、EC2、その他のAWSサービスへの接続確認を行います
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_s3_connection():
    """S3サービスへの接続テスト"""
    print("\n--- S3接続テスト ---")
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        print(f"✅ S3接続成功! バケット数: {len(buckets)}")
        
        for bucket in buckets[:5]:  # 最初の5個のバケットを表示
            print(f"  - {bucket['Name']} (作成日: {bucket['CreationDate'].strftime('%Y-%m-%d')})")
        
        if len(buckets) > 5:
            print(f"  ... 他 {len(buckets) - 5} 個のバケット")
            
        return True
        
    except ClientError as e:
        print(f"❌ S3接続エラー: {e}")
        return False

def test_ec2_connection():
    """EC2サービスへの接続テスト"""
    print("\n--- EC2接続テスト ---")
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.describe_instances()
        
        instances = []
        for reservation in response['Reservations']:
            instances.extend(reservation['Instances'])
        
        print(f"✅ EC2接続成功! インスタンス数: {len(instances)}")
        
        state_counts = {}
        for instance in instances:
            state = instance['State']['Name']
            state_counts[state] = state_counts.get(state, 0) + 1
        
        for state, count in state_counts.items():
            print(f"  - {state}: {count}個")
            
        return True
        
    except ClientError as e:
        print(f"❌ EC2接続エラー: {e}")
        return False

def test_regions():
    """利用可能リージョンの確認"""
    print("\n--- リージョン確認テスト ---")
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.describe_regions()
        
        regions = [region['RegionName'] for region in response['Regions']]
        print(f"✅ リージョン確認成功! 利用可能リージョン数: {len(regions)}")
        
        current_region = boto3.Session().region_name
        print(f"現在のリージョン: {current_region}")
        
        return True
        
    except ClientError as e:
        print(f"❌ リージョン確認エラー: {e}")
        return False

def verify_service_connections():
    """サービス接続確認のメイン関数"""
    print("=== ステップ2: サービス接続テスト ===")
    
    results = []
    results.append(test_s3_connection())
    results.append(test_ec2_connection())
    results.append(test_regions())
    
    success_count = sum(results)
    total_tests = len(results)
    
    print(f"\n=== 結果: {success_count}/{total_tests} のテストが成功 ===")
    
    return all(results)

if __name__ == "__main__":
    success = verify_service_connections()
    exit(0 if success else 1)
