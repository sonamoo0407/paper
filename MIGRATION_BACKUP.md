# VirtualBox → VMware 이관 안전 백업

- 백업 브랜치: `backup/hermes-vm-migration-20260928`
- 기준 원격: `https://github.com/sonamoo0407/paper.git`
- 분리 checkout의 기준 커밋: `aa9131f570e5c3de2dffd07428d90beb3f82b61b`
- 애플리케이션 소스 기준 커밋: `aef47b4503f9ed31765b81e0d9043f1e14cd6768`
- 문서 기준 커밋: `0e486b3d197dabe0c5385dccb56e10f5878351ba`

## 포함 범위

모든 이관 파일은 `vm-migration-backup-20260928/` 아래에만 넣었다. 기존 원격 `main`과 기존 로컬 checkout은 변경하지 않는다.

- `source/` — 현재 프로젝트의 Python 소스, 스크립트, 테스트, 프로젝트 스킬, README, 검수 문서
- `source-docs-branch/` — 현재 문서 브랜치의 `docs/`, README, VALIDATION 기록
- `hermes-profile/skills/` — 이 연구 흐름에 사용한 비밀 없는 Hermes 스킬 원본
- `hermes-profile/memories/USER.md`, `MEMORY.md` — 비밀 패턴 검사 후 포함한 사용자 선호·작업 메모
- `hermes-profile/CONFIG_STRUCTURE.md` — `~/.hermes/config.yaml`의 **키 구조만** 기록한 파일; 모든 값은 제외
- `graph-renderer/` — 인용 입력 JSON, graph JSON, 두 독립 HTML 렌더러, UI 검수 결과 JSON 및 보고서
- `FILE_INVENTORY.tsv` — 위 68개 파일의 상대 경로, 바이트 수, SHA-256

`FILE_INVENTORY.tsv` SHA-256:

```text
ce2ea64371142cfa6f18f41fbd3713dbe78c6a735a89becebb423abc1323f69d
```

이 문서와 인벤토리 파일 자신은 자기참조 해시 문제를 피하기 위해 목록의 대상에서 제외했다. 이관 후에는 다음으로 각각 확인한다.

```bash
sha256sum MIGRATION_BACKUP.md vm-migration-backup-20260928/FILE_INVENTORY.tsv
```

## 명시적 제외와 이유

- API 키·토큰·비밀번호·Discord 인증·OAuth/인증 파일: 비밀정보이므로 제외
- `.env`, `auth.json`, `state.db`, `sessions/`, `logs/`, 로그인 쿠키·프록시 세션: 자격증명·개인 세션·실행 기록을 포함할 수 있어 제외
- `config.yaml` 원문: 설정값에 민감한 연결 정보가 있을 수 있어 제외. 구조만 `CONFIG_STRUCTURE.md`에 보존
- `.venv`, `venv`, `node_modules`, Python/도구 캐시, 임시 WebDriver·브라우저 산출물: 운영체제·환경 의존 또는 재생성 가능하므로 제외
- `vendor/`: 제3자 대형 소스 트리이며 이관 후 잠금 파일/공식 배포본으로 재구성하는 편이 안전하므로 제외
- 대용량 원문 PDF, `pdfs/`, `raw-metadata/`: 저작권·용량·개인 연구 데이터 경계 때문에 제외
- 원본 연구 run 전체: PDF·raw response·캐시를 포함할 수 있어 제외. 대신 작은 graph JSON/HTML과 검수 기록만 포함

## 복원 절차

1. VMware 환경에서 Git과 Python 3.11 이상을 설치한다.
2. 새 작업 위치에서 이 백업 브랜치만 clone한다.

   ```bash
   git clone --branch backup/hermes-vm-migration-20260928 --single-branch \
     https://github.com/sonamoo0407/paper.git paper-migration
   cd paper-migration
   ```

3. 포함 목록과 해시를 검증한다.

   ```bash
   cd vm-migration-backup-20260928
   python3 - <<'PY'
   from pathlib import Path
   import hashlib
   for line in Path('FILE_INVENTORY.tsv').read_text(encoding='utf-8').splitlines()[1:]:
       rel, size, expected = line.split('\t')
       p = Path(rel)
       actual = hashlib.sha256(p.read_bytes()).hexdigest()
       assert actual == expected and p.stat().st_size == int(size), rel
   print('inventory hash verification: PASS')
   PY
   ```

4. 애플리케이션을 복원할 새 작업 폴더에 `source/`의 내용을 복사한다. 가상환경은 복사하지 말고 새로 만들고, 프로젝트의 `README.md`에 적힌 설치·테스트 절차를 따른다.
5. Hermes는 새 환경에서 공식 설치/로그인 절차를 사용한다. `hermes-profile/skills/`는 기존 동명 스킬을 덮어쓰지 말고 비교 후 필요한 것만 설치한다. `CONFIG_STRUCTURE.md`는 값 없는 구조 참고용이며 실행 설정 파일로 사용하지 않는다.
6. API 키, Discord 인증, 로그인 쿠키, 프록시·구독 DB 세션은 새 VMware 환경에서 사용자가 직접 설정한다. 이 백업에서 복원하지 않는다.
7. 그래프 UI는 `graph-renderer/` 안의 HTML과 JSON만으로 로컬 정적 서버에서 재검수할 수 있다. 외부 URL·API 요청을 하지 않는지 다시 관찰한다.

## 이관 전 검증

- stage 전 `git diff --cached` 확인
- stage 된 텍스트에 secret-shaped 값·`.env`·인증/세션/대용량 PDF가 없는지 검사
- 새 브랜치만 push 후 원격 ref를 재조회
