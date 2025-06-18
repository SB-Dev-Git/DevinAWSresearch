#!/usr/bin/env python3
"""
ステップ3（難）: 包括的検証システム
複数リージョン、IAM権限、エラーハンドリングを含む包括的なAWS接続検証
"""

import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from concurrent.futures import ThreadPoolExecutor, as_completed

class AWSComprehensiveVerifier:
    def __init__(self):
        self.session = boto3.Session()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
    
    def log_test_result(self, test_name, success, details=None, error=None):
        """テスト結果をログに記録"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'error': str(error) if error else None
        }
        self.results['tests'].append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
        if error:
            print(f"    エラー: {error}")
    
    def test_iam_permissions(self):
        """IAM権限の詳細確認"""
        print("\n--- IAM権限確認 ---")
        
        try:
            iam_client = self.session.client('iam')
            sts_client = self.session.client('sts')
            
            caller_identity = sts_client.get_caller_identity()
            user_arn = caller_identity['Arn']
            
            details = {
                'user_arn': user_arn,
                'account_id': caller_identity['Account']
            }
            
            if ':user/' in user_arn:
                username = user_arn.split('/')[-1]
                try:
                    attached_policies = iam_client.list_attached_user_policies(UserName=username)
                    details['attached_policies_count'] = len(attached_policies['AttachedPolicies'])
                    
                    inline_policies = iam_client.list_user_policies(UserName=username)
                    details['inline_policies_count'] = len(inline_policies['PolicyNames'])
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDenied':
                        details['iam_access'] = 'アクセス拒否（IAM読み取り権限なし）'
                    else:
                        raise
            
            self.log_test_result("IAM権限確認", True, details)
            return True
            
        except Exception as e:
            self.log_test_result("IAM権限確認", False, error=e)
            return False
    
    def test_region_connectivity(self, region_name):
        """指定リージョンでの接続テスト"""
        try:
            ec2_client = self.session.client('ec2', region_name=region_name)
            
            response = ec2_client.describe_availability_zones()
            az_count = len(response['AvailabilityZones'])
            
            return {
                'region': region_name,
                'success': True,
                'availability_zones': az_count
            }
            
        except Exception as e:
            return {
                'region': region_name,
                'success': False,
                'error': str(e)
            }
    
    def test_multi_region_connectivity(self):
        """複数リージョンでの並列接続テスト"""
        print("\n--- 複数リージョン接続テスト ---")
        
        test_regions = [
            'ap-northeast-1',  # 東京
            'us-east-1',       # バージニア北部
            'eu-west-1',       # アイルランド
            'ap-southeast-1',  # シンガポール
            'us-west-2'        # オレゴン
        ]
        
        try:
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_region = {
                    executor.submit(self.test_region_connectivity, region): region 
                    for region in test_regions
                }
                
                results = []
                for future in as_completed(future_to_region):
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        print(f"  ✅ {result['region']}: AZ数 {result['availability_zones']}")
                    else:
                        print(f"  ❌ {result['region']}: {result['error']}")
            
            successful_regions = [r for r in results if r['success']]
            details = {
                'tested_regions': len(test_regions),
                'successful_regions': len(successful_regions),
                'success_rate': f"{len(successful_regions)}/{len(test_regions)}"
            }
            
            self.log_test_result("複数リージョン接続テスト", len(successful_regions) > 0, details)
            return len(successful_regions) > 0
            
        except Exception as e:
            self.log_test_result("複数リージョン接続テスト", False, error=e)
            return False
    
    def test_service_limits(self):
        """サービス制限の確認"""
        print("\n--- サービス制限確認 ---")
        
        try:
            ec2_client = self.session.client('ec2')
            
            vpcs = ec2_client.describe_vpcs()
            vpc_count = len(vpcs['Vpcs'])
            
            security_groups = ec2_client.describe_security_groups()
            sg_count = len(security_groups['SecurityGroups'])
            
            details = {
                'vpc_count': vpc_count,
                'security_group_count': sg_count,
                'vpc_limit_check': 'OK' if vpc_count < 5 else '制限に近い'
            }
            
            self.log_test_result("サービス制限確認", True, details)
            return True
            
        except Exception as e:
            self.log_test_result("サービス制限確認", False, error=e)
            return False
    
    def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n--- エラーハンドリングテスト ---")
        
        try:
            s3_client = self.session.client('s3')
            
            try:
                s3_client.head_bucket(Bucket='non-existent-bucket-12345-test')
                details = {'error_handling': '予期しない成功'}
                success = False
            except ClientError as e:
                if e.response['Error']['Code'] in ['404', 'NoSuchBucket']:
                    details = {'error_handling': '正常にエラーをキャッチ', 'error_code': e.response['Error']['Code']}
                    success = True
                else:
                    details = {'error_handling': '予期しないエラー', 'error_code': e.response['Error']['Code']}
                    success = False
            
            self.log_test_result("エラーハンドリングテスト", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("エラーハンドリングテスト", False, error=e)
            return False
    
    def generate_report(self):
        """検証結果レポートの生成"""
        successful_tests = [t for t in self.results['tests'] if t['success']]
        total_tests = len(self.results['tests'])
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': len(successful_tests),
            'success_rate': f"{len(successful_tests)}/{total_tests}",
            'overall_success': len(successful_tests) == total_tests
        }
        
        print(f"\n=== 包括的検証結果レポート ===")
        print(f"実行時刻: {self.results['timestamp']}")
        print(f"総テスト数: {total_tests}")
        print(f"成功テスト数: {len(successful_tests)}")
        print(f"成功率: {self.results['summary']['success_rate']}")
        print(f"総合結果: {'✅ 成功' if self.results['summary']['overall_success'] else '❌ 一部失敗'}")
        
        report_filename = f"aws_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"詳細レポート: {report_filename}")
        
        return self.results['summary']['overall_success']

def verify_comprehensive():
    """包括的検証のメイン関数"""
    print("=== ステップ3: 包括的検証システム ===")
    
    verifier = AWSComprehensiveVerifier()
    
    verifier.test_iam_permissions()
    verifier.test_multi_region_connectivity()
    verifier.test_service_limits()
    verifier.test_error_handling()
    
    return verifier.generate_report()

if __name__ == "__main__":
    success = verify_comprehensive()
    exit(0 if success else 1)
