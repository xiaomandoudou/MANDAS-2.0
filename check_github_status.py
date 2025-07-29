#!/usr/bin/env python3
"""
GitHub Actions状态检查脚本
用于检查PR的CI/CD状态和测试结果
"""

import requests
import json
import sys
import time
from datetime import datetime

class GitHubStatusChecker:
    def __init__(self, repo_owner, repo_name, token=None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.base_url = "https://api.github.com"
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MANDAS-Test-Checker"
        }
        
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def get_pr_status(self, pr_number):
        """获取PR的状态"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取PR状态失败: {e}")
            return None
    
    def get_pr_checks(self, pr_number):
        """获取PR的检查状态"""
        # 首先获取PR信息以获取HEAD SHA
        pr_info = self.get_pr_status(pr_number)
        if not pr_info:
            return None
        
        head_sha = pr_info["head"]["sha"]
        
        # 获取检查运行
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/commits/{head_sha}/check-runs"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取检查状态失败: {e}")
            return None
    
    def get_pr_status_checks(self, pr_number):
        """获取PR的状态检查"""
        pr_info = self.get_pr_status(pr_number)
        if not pr_info:
            return None
        
        head_sha = pr_info["head"]["sha"]
        
        # 获取状态检查
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/commits/{head_sha}/status"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取状态检查失败: {e}")
            return None
    
    def display_pr_summary(self, pr_number):
        """显示PR摘要"""
        pr_info = self.get_pr_status(pr_number)
        if not pr_info:
            return False
        
        print(f"\n🔍 PR #{pr_number} 状态摘要")
        print("=" * 50)
        print(f"标题: {pr_info['title']}")
        print(f"状态: {pr_info['state']}")
        print(f"作者: {pr_info['user']['login']}")
        print(f"创建时间: {pr_info['created_at']}")
        print(f"更新时间: {pr_info['updated_at']}")
        print(f"可合并: {'✅' if pr_info['mergeable'] else '❌' if pr_info['mergeable'] is False else '⏳'}")
        
        return True
    
    def display_check_runs(self, pr_number):
        """显示检查运行状态"""
        checks = self.get_pr_checks(pr_number)
        if not checks:
            print("⚠️  无法获取检查运行信息")
            return False
        
        print(f"\n🔧 GitHub Actions 检查运行")
        print("=" * 50)
        
        if not checks.get("check_runs"):
            print("📝 暂无检查运行")
            return True
        
        for check in checks["check_runs"]:
            status_icon = {
                "completed": "✅" if check["conclusion"] == "success" else "❌",
                "in_progress": "⏳",
                "queued": "⏸️"
            }.get(check["status"], "❓")
            
            print(f"{status_icon} {check['name']}")
            print(f"   状态: {check['status']}")
            if check["status"] == "completed":
                print(f"   结果: {check['conclusion']}")
            print(f"   开始时间: {check['started_at']}")
            if check.get("completed_at"):
                print(f"   完成时间: {check['completed_at']}")
            print()
        
        return True
    
    def display_status_checks(self, pr_number):
        """显示状态检查"""
        status = self.get_pr_status_checks(pr_number)
        if not status:
            print("⚠️  无法获取状态检查信息")
            return False
        
        print(f"\n📊 状态检查")
        print("=" * 50)
        
        overall_state = status.get("state", "unknown")
        state_icon = {
            "success": "✅",
            "failure": "❌",
            "error": "💥",
            "pending": "⏳"
        }.get(overall_state, "❓")
        
        print(f"总体状态: {state_icon} {overall_state}")
        
        if status.get("statuses"):
            print("\n详细状态:")
            for check in status["statuses"]:
                check_icon = {
                    "success": "✅",
                    "failure": "❌",
                    "error": "💥",
                    "pending": "⏳"
                }.get(check["state"], "❓")
                
                print(f"{check_icon} {check['context']}: {check['description']}")
        else:
            print("📝 暂无状态检查")
        
        return True
    
    def wait_for_checks(self, pr_number, timeout=1800):  # 30分钟超时
        """等待检查完成"""
        print(f"\n⏳ 等待PR #{pr_number}的检查完成...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            checks = self.get_pr_checks(pr_number)
            status = self.get_pr_status_checks(pr_number)
            
            if not checks and not status:
                print("❌ 无法获取检查状态")
                return False
            
            # 检查GitHub Actions
            all_completed = True
            if checks and checks.get("check_runs"):
                for check in checks["check_runs"]:
                    if check["status"] != "completed":
                        all_completed = False
                        break
            
            # 检查状态检查
            status_completed = True
            if status and status.get("state") == "pending":
                status_completed = False
            
            if all_completed and status_completed:
                print("✅ 所有检查已完成")
                return True
            
            print(f"⏳ 检查进行中... (已等待 {int(time.time() - start_time)} 秒)")
            time.sleep(30)  # 每30秒检查一次
        
        print("⏰ 等待超时")
        return False
    
    def check_pr_ready_to_merge(self, pr_number):
        """检查PR是否准备好合并"""
        pr_info = self.get_pr_status(pr_number)
        checks = self.get_pr_checks(pr_number)
        status = self.get_pr_status_checks(pr_number)
        
        if not pr_info:
            return False
        
        print(f"\n🎯 PR #{pr_number} 合并就绪检查")
        print("=" * 50)
        
        ready_to_merge = True
        
        # 检查PR状态
        if pr_info["state"] != "open":
            print("❌ PR未处于开放状态")
            ready_to_merge = False
        else:
            print("✅ PR处于开放状态")
        
        # 检查可合并性
        if pr_info["mergeable"] is False:
            print("❌ PR存在合并冲突")
            ready_to_merge = False
        elif pr_info["mergeable"] is True:
            print("✅ PR可以合并")
        else:
            print("⏳ 合并状态检查中")
        
        # 检查GitHub Actions
        if checks and checks.get("check_runs"):
            failed_checks = [
                check for check in checks["check_runs"]
                if check["status"] == "completed" and check["conclusion"] != "success"
            ]
            
            if failed_checks:
                print(f"❌ {len(failed_checks)} 个检查失败")
                ready_to_merge = False
            else:
                print("✅ 所有GitHub Actions检查通过")
        
        # 检查状态检查
        if status:
            if status.get("state") == "success":
                print("✅ 所有状态检查通过")
            elif status.get("state") in ["failure", "error"]:
                print("❌ 状态检查失败")
                ready_to_merge = False
            elif status.get("state") == "pending":
                print("⏳ 状态检查进行中")
                ready_to_merge = False
        
        print(f"\n{'🎉 PR准备就绪，可以合并！' if ready_to_merge else '⚠️  PR尚未准备好合并'}")
        
        return ready_to_merge

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_github_status.py <PR_NUMBER> [--wait] [--token TOKEN]")
        sys.exit(1)
    
    pr_number = int(sys.argv[1])
    wait_for_completion = "--wait" in sys.argv
    
    # 获取token（如果提供）
    token = None
    if "--token" in sys.argv:
        token_index = sys.argv.index("--token") + 1
        if token_index < len(sys.argv):
            token = sys.argv[token_index]
    
    # 创建检查器
    checker = GitHubStatusChecker("xiaomandoudou", "MANDAS-2.0", token)
    
    # 显示PR摘要
    if not checker.display_pr_summary(pr_number):
        sys.exit(1)
    
    # 显示检查状态
    checker.display_check_runs(pr_number)
    checker.display_status_checks(pr_number)
    
    # 如果需要等待，等待检查完成
    if wait_for_completion:
        checker.wait_for_checks(pr_number)
    
    # 检查是否准备好合并
    ready = checker.check_pr_ready_to_merge(pr_number)
    
    sys.exit(0 if ready else 1)

if __name__ == "__main__":
    main()
