# src/evaluation/fact_checker.py
import re
from typing import Dict, List, Set, Tuple

class FactChecker:
    """檢查 LLM 回答中的數值是否來自檢索結果"""
    
    @staticmethod
    def verify_facts(
        llm_answer: str,
        retrieved_facts: List[Dict],
        tolerance: float = 0.1
    ) -> Dict:
        """
        驗證 LLM 回答的事實一致性
        
        改進：
        1. 支援單位轉換（0.285 ≈ 28.5%）
        2. 允許簡單衍生計算（差值）
        3. 詳細輸出違規內容
        """
        # 1. 從 LLM 回答中抽取數值
        answer_numbers = FactChecker._extract_numbers(llm_answer)
        
        # 2. 從檢索結果中收集所有數值
        fact_numbers = set()
        for hit in retrieved_facts:
            stats = hit.get("stats", {})
            for value in stats.values():
                try:
                    num = float(value)
                    fact_numbers.add(num)
                except (ValueError, TypeError):
                    continue
        
        # 3. 計算可能的衍生數值
        derived_numbers = FactChecker._find_derived_numbers(fact_numbers)
        
        # 4. 檢查每個數值
        violations = []
        verified_count = 0
        
        for num, context in answer_numbers:
            # 檢查是否在事實中（含單位轉換）
            if FactChecker._is_in_facts(num, fact_numbers, tolerance):
                verified_count += 1
                continue
            
            # 檢查是否是衍生計算
            if FactChecker._is_derived(num, derived_numbers, tolerance):
                verified_count += 1
                continue
            
            # 真的是幻覺
            violations.append({
                "value": num,
                "context": context,
                "message": f"數值 {num} 未在檢索結果中找到"
            })
        
        total = len(answer_numbers)
        confidence = verified_count / total if total > 0 else 1.0
        
        return {
            "is_consistent": len(violations) == 0,
            "violations": [v["message"] for v in violations],
            "violation_details": violations,  # 詳細資訊
            "confidence": confidence,
            "hallucination_count": len(violations),
            "total_numbers": total,
            "verified_numbers": verified_count
        }
    
    @staticmethod
    def _extract_numbers(text: str) -> List[Tuple[float, str]]:
        """
        從文本中抽取所有數值及其上下文
        
        Returns:
            List of (number, context)
        """
        pattern = r'\b(\d+\.?\d*)\s*[%％]?'
        matches = re.finditer(pattern, text)
        
        numbers = []
        for match in matches:
            try:
                num = float(match.group(1))
                
                # 取得上下文（前後 30 字元）
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                numbers.append((num, context))
            except ValueError:
                continue
        
        return numbers
    
    @staticmethod
    def _is_in_facts(num: float, fact_numbers: Set[float], tolerance: float) -> bool:
        """
        檢查數值是否在事實中（支援單位轉換）
        """
        # 1. 直接匹配
        if any(abs(num - fact) <= abs(fact * tolerance) for fact in fact_numbers):
            return True
        
        # 2. 百分比 → 小數（28.5 → 0.285）
        if any(abs(num/100 - fact) <= abs(fact * tolerance) for fact in fact_numbers):
            return True
        
        # 3. 小數 → 百分比（0.285 → 28.5）
        if any(abs(num*100 - fact) <= abs(fact * tolerance) for fact in fact_numbers):
            return True
        
        return False
    
    @staticmethod
    def _find_derived_numbers(fact_numbers: Set[float]) -> Set[float]:
        """
        計算可能的衍生數值（差值、比率）
        
        例如：K% 從 32.1 降到 28.5 → 差值 3.6
        """
        derived = set()
        facts_list = sorted(fact_numbers)
        
        # 計算所有可能的差值
        for i, a in enumerate(facts_list):
            for b in facts_list[i+1:]:
                diff = abs(a - b)
                derived.add(round(diff, 2))
                derived.add(round(diff, 3))
        
        return derived
    
    @staticmethod
    def _is_derived(num: float, derived_numbers: Set[float], tolerance: float) -> bool:
        """檢查是否為衍生數值"""
        return any(
            abs(num - derived) <= 0.1
            for derived in derived_numbers
        )