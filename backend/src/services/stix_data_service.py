"""
STIX ATT&CK 数据服务

使用 stix2 库从本地 attack-stix-data Git 子模块加载和查询 ATT&CK 数据。
替代原有的 MITREAPIService，提供本地化的 STIX 数据访问。

参考文档: attack-stix-data/USAGE.md
"""
from stix2 import MemoryStore, Filter
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class STIXDataService:
    """STIX ATT&CK 数据服务"""

    def __init__(self, stix_file_path: Optional[Path] = None):
        """
        初始化 STIX 数据服务

        参数说明:
            stix_file_path: STIX JSON 文件路径，默认为最新版本

        数据源:
            attack-stix-data/enterprise-attack/enterprise-attack.json
        """
        if stix_file_path is None:
            # 默认使用项目中的最新版本
            project_root = Path(__file__).parent.parent.parent.parent
            stix_file_path = project_root / "attack-stix-data" / "enterprise-attack" / "enterprise-attack.json"

        self.stix_file_path = stix_file_path

        # 验证文件存在
        if not self.stix_file_path.exists():
            raise FileNotFoundError(f"STIX 文件不存在: {self.stix_file_path}")

        # 加载 STIX 数据到 MemoryStore
        self.store = MemoryStore()
        self.store.load_from_file(str(self.stix_file_path))

        logger.info(f"已加载 STIX 数据: {self.stix_file_path}")

    def _filter_revoked_deprecated(self, objects: List) -> List:
        """
        过滤已撤销和已弃用的对象

        参考: attack-stix-data/USAGE.md "Handling Revoked and Deprecated Objects"

        参数:
            objects: STIX 对象列表

        返回:
            过滤后的对象列表
        """
        return [
            obj for obj in objects
            if not obj.get('x_mitre_deprecated', False)
            and not obj.get('revoked', False)
        ]

    # ===== 战术相关 =====

    def get_all_tactics(self) -> List[Dict[str, Any]]:
        """
        获取所有战术

        返回:
            战术对象列表
        """
        tactics = self.store.query([
            Filter('type', '=', 'x-mitre-tactic')
        ])
        return self._filter_revoked_deprecated(tactics)

    def get_tactic_by_shortname(self, shortname: str) -> Optional[Dict]:
        """
        根据 shortname 获取战术

        参数:
            shortname: 战术 shortname (如 'reconnaissance', 'defense-evasion')

        返回:
            战术对象或 None
        """
        results = self.store.query([
            Filter('type', '=', 'x-mitre-tactic'),
            Filter('x_mitre_shortname', '=', shortname)
        ])
        filtered = self._filter_revoked_deprecated(results)
        return filtered[0] if filtered else None

    # ===== 技术相关 =====

    def get_all_techniques(self, include_subtechniques: bool = True) -> List[Dict]:
        """
        获取所有技术

        参数:
            include_subtechniques: 是否包含子技术

        返回:
            技术对象列表
        """
        if include_subtechniques:
            techniques = self.store.query([Filter('type', '=', 'attack-pattern')])
        else:
            techniques = self.store.query([
                Filter('type', '=', 'attack-pattern'),
                Filter('x_mitre_is_subtechnique', '=', False)
            ])
        return self._filter_revoked_deprecated(techniques)

    def get_technique_by_attack_id(self, attack_id: str) -> Optional[Dict]:
        """
        根据 ATT&CK ID (如 T1055) 获取技术

        参数:
            attack_id: ATT&CK 技术 ID (如 T1055, T1055.001)

        返回:
            技术对象或 None
        """
        results = self.store.query([
            Filter('type', '=', 'attack-pattern'),
            Filter('external_references.external_id', '=', attack_id)
        ])
        filtered = self._filter_revoked_deprecated(results)
        return filtered[0] if filtered else None

    def get_techniques_by_tactic(self, tactic_shortname: str) -> List[Dict]:
        """
        根据战术获取所有相关技术

        参数:
            tactic_shortname: 战术 shortname (如 'defense-evasion')

        返回:
            技术对象列表
        """
        techniques = self.store.query([
            Filter('type', '=', 'attack-pattern'),
            Filter('kill_chain_phases.phase_name', '=', tactic_shortname),
            Filter('kill_chain_phases.kill_chain_name', '=', 'mitre-attack')
        ])
        return self._filter_revoked_deprecated(techniques)

    def get_techniques_by_platform(self, platform: str) -> List[Dict]:
        """
        根据平台筛选技术

        参数:
            platform: 平台名称 (如 'Windows', 'Linux', 'macOS')

        返回:
            技术对象列表
        """
        techniques = self.store.query([
            Filter('type', '=', 'attack-pattern'),
            Filter('x_mitre_platforms', '=', platform)
        ])
        return self._filter_revoked_deprecated(techniques)

    def get_subtechniques_of(self, technique_id: str) -> List[Dict]:
        """
        获取指定技术的所有子技术

        参数:
            technique_id: STIX ID 或 ATT&CK ID

        返回:
            子技术对象列表
        """
        # 使用关系查询
        relationships = self.store.query([
            Filter('type', '=', 'relationship'),
            Filter('relationship_type', '=', 'subtechnique-of'),
            Filter('source_ref', '=', technique_id)
        ])

        subtechnique_ids = [r.target_ref for r in relationships if not r.revoked]
        return [self.store.get(stix_id) for stix_id in subtechnique_ids if self.store.get(stix_id)]

    # ===== 数据统计 =====

    def get_statistics(self) -> Dict[str, int]:
        """
        获取数据统计信息

        返回:
            统计信息字典
        """
        stats = {
            'tactics': len(self.get_all_tactics()),
            'techniques': len(self.get_all_techniques(include_subtechniques=False)),
            'subtechniques': len(self.get_all_techniques()) - len(self.get_all_techniques(include_subtechniques=False)),
        }

        logger.info(f"STIX 数据统计: {stats}")
        return stats


# 便捷函数
def get_stix_service() -> STIXDataService:
    """
    获取 STIX 服务实例（单例模式）

    返回:
        STIXDataService 实例
    """
    # 使用模块级变量实现单例
    if not hasattr(get_stix_service, '_instance'):
        get_stix_service._instance = STIXDataService()
    return get_stix_service._instance
