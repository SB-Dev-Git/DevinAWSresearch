#!/usr/bin/env python3
"""
ステップ1（易）: 基本認証確認
AWS認証情報の確認とユーザー情報の取得を行います
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def verify_basic_auth():
    """基本的なAWS認証確認を実行"""
    print("=== ステップ1: 基本認証確認 ===")
    
    try:
        sts_client = boto3.client('sts')
        
        response = sts_client.get_caller_identity()
        
        print("✅ AWS認証成功!")
        print(f"ユーザーID: {response['UserId']}")
        print(f"アカウントID: {response['Account']}")
        print(f"ARN: {response['Arn']}")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS認証情報が設定されていません")
        print("aws configureコマンドで認証情報を設定してください")
        return False
        
    except ClientError as e:
        print(f"❌ AWS認証エラー: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = verify_basic_auth()
    exit(0 if success else 1)
