# 멍개미국어 — 릴리즈 키트

멍개 앱과 같은 구조입니다. 한 번만 세팅해 두면, 이후 릴리즈는 GitHub 웹에서 **버튼 한 번**으로 끝납니다.

---

## 1. 키스토어 생성 (최초 1회, 윈도우 PowerShell)

멍개 키스토어를 재사용하지 마십시오. 앱마다 별도 키가 원칙입니다. 한 키가 유출되거나 분실돼도 다른 앱이 영향을 받지 않습니다.

```powershell
cd "C:\Users\stcal"
& "$env:JAVA_HOME\bin\keytool.exe" -genkeypair -v `
  -keystore mungae-american-release.jks `
  -alias mungae-american `
  -keyalg RSA -keysize 2048 -validity 10950 `
  -storetype PKCS12 `
  -dname "CN=Youngjae Jung, O=JNP Solution, L=Beijing, C=KR"
```

비밀번호를 물어보면 하나를 정해 입력하십시오. 키스토어 비밀번호와 키 비밀번호를 같게 두면 관리가 편합니다.

> **이 파일을 잃어버리면 앱을 영원히 업데이트할 수 없습니다.** 구글 플레이는 같은 키로 서명된 APK만 같은 앱으로 인정합니다.
> `mungae-american-release.jks` 파일과 비밀번호를 구글 드라이브 등 PC 바깥 두 곳 이상에 보관하십시오. 저장소에는 절대 올리지 마십시오.

## 2. base64로 변환

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Users\stcal\mungae-american-release.jks")) | Set-Clipboard
```

클립보드에 긴 문자열이 복사됩니다.

## 3. GitHub Secrets 4개 등록

저장소 → Settings → Secrets and variables → Actions → New repository secret

| 이름 | 값 |
|---|---|
| `KEYSTORE_BASE64` | 2번에서 복사한 문자열 |
| `KEYSTORE_PASSWORD` | 키스토어 비밀번호 |
| `KEY_ALIAS` | `mungae-american` |
| `KEY_PASSWORD` | 키 비밀번호 |

## 4. 파일 배치

```
저장소 루트/
├─ version.properties              ← 이 키트의 파일
├─ .github/workflows/release.yml   ← 이 키트의 파일
└─ app/build.gradle.kts            ← 이 키트의 build.gradle.kts
```

---

## 릴리즈하는 법

Actions 탭 → 왼쪽에서 **Release** 선택 → **Run workflow** →

- **올릴 자리**: `patch`(1.0.0 → 1.0.1) / `minor`(→ 1.1.0) / `major`(→ 2.0.0)
- **릴리즈 노트**: 한 줄로 적거나, 비워두면 커밋 목록이 자동으로 들어갑니다

버튼을 누르면 순서대로 진행됩니다.

1. `version.properties`의 버전과 versionCode를 올림
2. 시크릿에서 키스토어를 복원해 AAB + APK를 서명 빌드
3. `apksigner`로 서명 인증서 검증 (여기서 실패하면 배포가 중단됩니다)
4. `mungae-american-1.0.1.aab` / `.apk`로 이름 정리
5. 버전 커밋 + `v1.0.1` 태그 푸시
6. GitHub Release 생성 및 파일 첨부
7. 러너에 복원했던 키스토어 삭제

versionCode는 자릿수와 무관하게 매 릴리즈 +1 이므로 구글 플레이 업로드에서 충돌이 나지 않습니다.

## 사고를 막는 규칙 세 가지

- `version.properties`를 손으로 고치지 마십시오. 워크플로우가 유일한 수정자입니다. 손으로 고치면 versionCode가 꼬여 플레이 업로드가 막힙니다.
- `release.jks`는 `.gitignore`에 넣으십시오. 러너에서도 마지막 단계에서 지웁니다.
- 비밀번호는 시크릿에만 두고 워크플로우 파일에 적지 마십시오. 로그에도 남지 않습니다.

제작: JNP Solution / 정영재 (Marvin Jung)
