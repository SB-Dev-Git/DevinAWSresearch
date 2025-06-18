#!/usr/bin/env python3
"""
全ステップ実行スクリプト
3つの検証ステップを順番に実行します
"""

import subprocess
import sys
import os

def run_script(script_name, step_description):
    """指定されたスクリプトを実行"""
    print(f"\n{'='*50}")
    print(f"実行中: {step_description}")
    print(f"スクリプト: {script_name}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True, 
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print(f"✅ {step_description} - 成功")
            return True
        else:
            print(f"❌ {step_description} - 失敗 (終了コード: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {step_description} - 実行エラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("AWS接続検証システム - 全ステップ実行")
    print("実行開始時刻:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    verification_steps = [
        ("step1_basic_auth.py", "ステップ1: 基本認証確認"),
        ("step2_service_connection.py", "ステップ2: サービス接続テスト"),
        ("step3_comprehensive_verification.py", "ステップ3: 包括的検証システム")
    ]
    
    results = []
    
    for script_name, description in verification_steps:
        if not os.path.exists(script_name):
            print(f"❌ スクリプトファイルが見つかりません: {script_name}")
            results.append(False)
            continue
            
        success = run_script(script_name, description)
        results.append(success)
        
        if success:
            print(f"次のステップまで2秒待機...")
            __import__('time').sleep(2)
        else:
            print(f"エラーが発生したため、次のステップに進みます...")
    
    print(f"\n{'='*60}")
    print("最終結果サマリー")
    print(f"{'='*60}")
    
    successful_steps = sum(results)
    total_steps = len(results)
    
    for i, (script_name, description) in enumerate(verification_steps):
        status = "✅ 成功" if results[i] else "❌ 失敗"
        print(f"{description}: {status}")
    
    print(f"\n総合結果: {successful_steps}/{total_steps} ステップが成功")
    
    if successful_steps == total_steps:
        print("🎉 すべての検証ステップが正常に完了しました！")
        return True
    else:
        print("⚠️  一部のステップで問題が発生しました。詳細を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
