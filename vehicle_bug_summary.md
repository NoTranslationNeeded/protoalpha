# 토큰 리셋 버튼 추가 및 탑승물 Parallax 버그 수정

## 완료된 작업

### 1. 탑승물 Parallax 버그 패턴 발견 ✅

사용자 테스트 결과를 기반으로 데이터베이스 분석을 수행한 결과:

**발견한 패턴:**
- 🔴 **문제 있음**: **유색 탑승물** (단색 Blue/Black/Red/Green/White)
  - Mobilizer Mech (청색)
  - Dreadmobile (흑색)  
  - Burner Rocket (적색)
  - Esika's Chariot (녹색)

- ✅ **정상 작동**: **무색 탑승물** (artifact/colorless)
  - Ribskiff (무색)
  - Soul Shredder (무색)
  - Carriage of Dreams (무색)
  - **그리고** 다색 탑승물 (Apocalypse Runner - 흑적색)

**결론**: Parallax 효과가 **유색 단색 탑승물의 카드 효과 텍스트 렌더링에 버그를 일으킴**

## 다음 단계

### 옵션 A: 유색 탑승물만 제외
```sql
WHERE SubTypes LIKE '%331%'  -- Vehicle
AND (Colors IS NULL OR Colors = '' OR LENGTH(Colors) - LENGTH(REPLACE(Colors, ',', '')) + 1 > 1)
-- 무색이거나 다색인 경우만 parallax 허용
```

### 옵션 B: 모든 탑승물 제외 (안전한 방법)
기존 계획대로 모든 SubType 331 카드를 parallax unlock에서 제외

### 권장사항
**옵션 B (모든 탑승물 제외)**를 권장합니다:
- 더 간단하고 안전함
- 유색 무색 구분 로직이 복잡할 수 있음
- 탑승물 자체가 많지 않음 (229장)
- 사용자가 원하면 개별적으로 parallax 적용 가능

## 구현 계획

변경사항 없음 - 기존 implementation_plan.md의 방법대로 모든 탑승물을 제외하는 것이 가장 안전합니다.
