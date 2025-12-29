"""
测试 manifest.json 解析器对 attck 字段的处理

测试场景:
1. 标准 Txxxx 格式
2. 带子技术 Txxxx.xxx 格式
3. 带描述的 Txxxx:[name] 格式
4. 带描述的子技术 Txxxx.xxx:[name] 格式
5. 中文描述 Txxxx:中文名称
6. 英文描述 Txxxx:English name
7. 无效格式
"""
import asyncio
import json
from pathlib import Path
import sys

# 添加项目路径
backend_src = Path(__file__).parent / "src"
sys.path.insert(0, str(backend_src))

from src.parsers.manifest_parser import ManifestParser


async def test_attck_parsing():
    """测试 attck 字段解析"""

    print("="*70)
    print("  测试 ATT&CK 字段解析")
    print("="*70)

    # 测试用例
    test_cases = [
        {
            "name": "标准格式 - T1055",
            "data": {
                "status": "completed",
                "alias": "TestFunction1",
                "summary": "Test function",
                "attck": ["T1055"]
            },
            "expected": ["T1055"],
            "should_pass": True
        },
        {
            "name": "子技术格式 - T1055.001",
            "data": {
                "status": "completed",
                "alias": "TestFunction2",
                "summary": "Test function",
                "attck": ["T1055.001"]
            },
            "expected": ["T1055.001"],
            "should_pass": True
        },
        {
            "name": "带中文描述 - T1055:进程注入",
            "data": {
                "status": "completed",
                "alias": "TestFunction3",
                "summary": "Test function",
                "attck": ["T1055:进程注入"]
            },
            "expected": ["T1055"],
            "should_pass": True
        },
        {
            "name": "带英文描述 - T1055:Process Injection",
            "data": {
                "status": "completed",
                "alias": "TestFunction4",
                "summary": "Test function",
                "attck": ["T1055:Process Injection"]
            },
            "expected": ["T1055"],
            "should_pass": True
        },
        {
            "name": "子技术带中文描述 - T1055.001:动态链接库注入",
            "data": {
                "status": "completed",
                "alias": "TestFunction5",
                "summary": "Test function",
                "attck": ["T1055.001:动态链接库注入"]
            },
            "expected": ["T1055.001"],
            "should_pass": True
        },
        {
            "name": "子技术带英文描述 - T1055.001:DLL Injection",
            "data": {
                "status": "completed",
                "alias": "TestFunction6",
                "summary": "Test function",
                "attck": ["T1055.001:DLL Injection"]
            },
            "expected": ["T1055.001"],
            "should_pass": True
        },
        {
            "name": "混合格式 - 多种类型",
            "data": {
                "status": "completed",
                "alias": "TestFunction7",
                "summary": "Test function",
                "attck": [
                    "T1055",
                    "T1055.001:动态链接库注入",
                    "T1106:Native API",
                    "T1480"
                ]
            },
            "expected": ["T1055", "T1055.001", "T1106", "T1480"],
            "should_pass": True
        },
        {
            "name": "无效格式 - X1234",
            "data": {
                "status": "completed",
                "alias": "TestFunction8",
                "summary": "Test function",
                "attck": ["X1234"]
            },
            "expected": None,
            "should_pass": False
        },
        {
            "name": "无效格式 - T123",
            "data": {
                "status": "completed",
                "alias": "TestFunction9",
                "summary": "Test function",
                "attck": ["T123"]
            },
            "expected": None,
            "should_pass": False
        }
    ]

    parser = ManifestParser(strict_mode=True)

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print("-" * 70)

        # 创建临时JSON文件
        temp_file = Path(f"/tmp/test_manifest_{i}.json")
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(test_case['data'], f, ensure_ascii=False, indent=2)

        try:
            result = await parser.parse_file(temp_file)

            print(f"原始 attck: {test_case['data']['attck']}")
            print(f"解析结果 attck: {result.data.get('attck', [])}")
            print(f"验证状态: {'✓ 通过' if result.is_valid else '✗ 失败'}")

            if result.is_valid:
                print(f"警告信息: {result.warnings}")

            # 验证结果
            if test_case['should_pass']:
                if result.is_valid:
                    if result.data.get('attck') == test_case['expected']:
                        print("✓ 测试通过")
                        passed += 1
                    else:
                        print(f"✗ 测试失败: 期望 {test_case['expected']}, 实际 {result.data.get('attck')}")
                        failed += 1
                else:
                    print(f"✗ 测试失败: 预期通过但实际失败")
                    print(f"  错误信息: {result.errors}")
                    failed += 1
            else:
                if not result.is_valid:
                    print("✓ 测试通过（正确识别无效格式）")
                    passed += 1
                else:
                    print("✗ 测试失败: 预期失败但实际通过")
                    failed += 1

        except Exception as e:
            print(f"✗ 测试异常: {str(e)}")
            failed += 1
        finally:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()

    print("\n" + "="*70)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_attck_parsing())
    sys.exit(0 if success else 1)
