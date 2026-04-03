# memoy_work

## 2026-04-04
- 사용자 요청: 로컬 코드베이스 구조 시각화 도구 구축 지시서 기반으로, 웹 표시 제외 단일 프로그램 분석기 형태 구현.
- 반영 사항:
  - codeviz-local 프로젝트 골격 생성
  - CLI 분석기 구현 (apps/cli/main.py)
  - 엔진 추상화 및 emerge 엔진 + 로컬 fallback 구현
  - 설정 파일 로더/스키마 구현
  - 경고 점검 로직(대용량 파일, 깊은 디렉터리, TODO/FIXME, 잠재 비밀키 패턴, 테스트/README 부재)
  - 실행 이력 저장(outputs/run_history.jsonl), run 요약/로그 저장
  - 문서 인덱스/버전 매니페스트 작성
  - help 연락처에 swh@speefox.com / 신우혁 반영
- 미완료/확인 필요:
  - GitHub 신규 레포지토리 생성(원칙 16) 사용자 승인 및 계정/원격 정보 필요
  - Emerge 설치 여부에 따른 실제 엔진 실행 검증 필요

### 실행 검증 결과
- 명령: `$env:PYTHONPATH='E:\code visualize\codeviz-local'; python -m apps.cli.main --config E:\code visualize\codeviz-local\configs\default.yaml`
- 결과: 성공(run_id=20260404_073635), `emerge` 미설치로 filesystem fallback 사용
- 산출물: outputs/runs/20260404_073635/{summary.json,warnings.json,run.log,fallback_summary.json}
- 정적 문법 체크: py_compile 통과

### 추가 수정
- `core/runner/analyze.py`: `output_dir` 설정값을 실제 latest 경로 계산에 반영
- `core/engine/emerge_engine.py`: fallback 스캔 시 제외 패턴을 config.exclude 기준으로 반영

### 재검증
- run_id=20260404_075031 성공
- engine_used=filesystem-fallback (emerge 미설치)
- 요약 파일: outputs/runs/20260404_075031/summary.json

### GUI 추가
- `apps/desktop/gui.py` Tkinter 기반 로컬 GUI 추가
- 기능: 프로젝트/설정 파일 선택, 엔진 선택, 분석 실행, 경고/요약 JSON 표시
- Help 메뉴에 연락처/제작자 정보 반영

### GitHub 연동
- 원격 저장소: https://github.com/Jolrin-Saram/code-struct-analysis-.git
- main 브랜치 초기 푸시 완료

### 위험 시각화 기능 강화
- 대상 코드 수정 없이 read-only 스캔으로 위험 라인 탐지 추가
- 산출물: risk_findings.json, risk_heatmap.json
- GUI에 Risk Visualization 탭 추가(파일별 히트맵 + 라인별 위험 목록)

### 코드 전용 분석 범위 강화
- 대상 파일 범위를 코드 확장자로 제한 (C/C++/Header/Python/Java/R)
- Python 확장자 추가: .pyw, .pyi, .pyx, .pxd
- 제외 패턴 강화: .vs, x64, Debug, Release, bin, obj 등
- 위험->오류 가능 경로 flowchart 생성: risk_flowchart.mmd
- GUI에 Error Flowchart(Mermaid) 표시 탭 추가

### 배포/시각화 확인
- 커밋: e246f82 (code-only risk visualization with flowchart output)
- 원격 반영: origin/main push 완료
- GUI 실행 확인: run_gui.ps1 직접 실행 시 타임아웃(창 이벤트 루프 유지)으로 정상 기동 패턴 확인
- 산출물 확인: risk_heatmap.json / risk_findings.json / risk_flowchart.mmd 생성 확인
