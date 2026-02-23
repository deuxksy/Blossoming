# Blossoming

> **AI** 를 활용해 생성된 프로젝트입니다.

세로 이미지를 가로 16:9 비율로 우아하게 넓히는 도구

## 빠른 시작

```bash
# Python 버전 (권장 - 가장 빠름)
python3 widen_gracefully.py 입력파일.jpg

# uv 사용 (의존성 없이 실행)
uv run widen_gracefully.py 입력파일.jpg

# uvx 사용 (단일 실행)
uvx --from Pillow,numpy,opencv-python widen_gracefully.py 입력파일.jpg

# Go 버전 (단일 바이너리 - 배포 용이)
./widen-gracefully-go 입력파일.jpg

# Shell 버전 (대안)
chmod +x widen-gracefully-memory.sh
./widen-gracefully-memory.sh 입력파일.jpg
```

## 이 도구가 하는 일

- **이미지 방향 감지**: 세로/가로/정방형 자동 감지 및 조건부 처리
- **세로형 이미지**:
  - 워터마크 제거: 하단 워터마크를 블러처리로 자연스럽게 제거
  - 여백 제거: 상하 불필요한 여백을 자동으로 제거
  - 16:9 변환: 좌우 블러 확장으로 자연스럽게 확장
- **가로형 이미지**:
  - 스마트 크롭: 얼굴/몸통 감지 기반 최적 크롭 (3단계 폴백)
  - 리사이즈: 3840x2160 해상도로 조정
- **정방형 이미지**: 자동 건너뜀
- **색감 보존**: 원본 색상 그대로 유지 (ICC 프로필)

## 설치

### Python 버전

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv pip install Pillow numpy opencv-python

# 또는 uv run으로 실행 (자동 의존성 관리)
uv run widen_gracefully.py 입력파일.jpg

# 또는 uvx로 단일 실행 (설치 불필요)
uvx --from Pillow,numpy,opencv-python widen_gracefully.py 입력파일.jpg
```

### Shell 버전

**요구 사항**: ImageMagick 7.0 이상

```bash
# 이미 ImageMagick이 설치되어 있다면 건너뜀
# 설치 확인
magick -version
```

**현재 버전**: ImageMagick 7.1.2-12 Q16-HDRI

### Go 버전

**요구 사항**: Go 1.20 이상

```bash
# 소스에서 빌드
go build -o widen-gracefully-go widen_gracefully.go

# 또는 미리 빌드된 바이너리 사용 (리눅스, macOS, 윈도우)
# 바이너리 다운로드 후 실행 권한 부여
chmod +x widen-gracefully-go
```

**현재 버전**: Go 1.23.4

## 사용법

### 단일 이미지 변환

```bash
# Python
python3 widen_gracefully.py ariel-introduction-04-10000px.jpg
# 결과: python/ariel-introduction-04-4k.jpg

# uv 사용
uv run widen_gracefully.py ariel-introduction-04-10000px.jpg

# uvx 사용 (의존성 없이 한번만 실행)
uvx --from Pillow,numpy,opencv-python widen_gracefully.py ariel-introduction-04-10000px.jpg

# Shell
./widen-gracefully-memory.sh ariel-introduction-04-10000px.jpg
# 결과: shell/ariel-introduction-04-4k.jpg
```

### 폴더 전체 변환 (추천)

폴더 경로를 지정하면 해당 폴더의 모든 이미지를 자동으로 처리합니다.

```bash
# Python
python3 widen_gracefully.py /path/to/images
# 결과: python/ 폴더에 모든 이미지가 변환됨

# uv 사용
uv run widen_gracefully.py /path/to/images

# uvx 사용 (의존성 없이 한번만 실행)
uvx --from Pillow,numpy,opencv-python widen_gracefully.py /path/to/images

# Shell
./widen-gracefully-memory.sh /path/to/images
# 결과: shell/ 폴더에 모든 이미지가 변환됨
```

**현재 폴더의 모든 이미지 처리**:
```bash
python3 widen_gracefully.py .
# 또는
uv run widen_gracefully.py .
# 또는
uvx --from Pillow,numpy,opencv-python widen_gracefully.py .
# 또는
./widen-gracefully-memory.sh .
```

**지원하는 파일 형식**: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif` (대소문자 무시)

**이미지 처리 규칙**:
- 세로형 (Portrait): 워터마크 제거 → 여백 제거 → 16:9 변환
- 가로형 (Landscape): 스마트 크롭 → 리사이즈
- 정방형 (Square): 자동 건너뜀

## 결과물

### 폴더 구조

```
temp/
├── python/              # Python 결과물
├── shell/               # Shell 결과물
└── go/                  # Go 결과물
```

### 변환 예시

| 원본 | 결과 | 해상도 |
|------|------|--------|
| 8708x11608 | python/ariel-introduction-04-4k.jpg | 3840x2160 |
| 8708x11608 | go/ariel-introduction-04-4k.jpg | 3840x2160 |
| 8708x11608 | shell/ariel-introduction-04-4k.jpg | 3840x2160 |

## 어떤 버전을 써야 하나요?

### uv 사용 (추천)
- **의존성 관리**: 자동으로 필요한 패키지 관리
- **가상 환경**: 프로젝트별 격리된 환경 제공
- **빠른 설치**: pip보다 훨씬 빠른 의존성 설치
- **프로젝트 관리**: 프로젝트 단위로 패키지 관리

### uvx 사용
- **일회성 실행**: 의존성 없이 한 번만 실행할 때
- **설치 불필요**: 시스템에 패키지 설치 없이 실행
- **테스트용**: 도구를 테스트하거나 시도해볼 때
- **가벼운 사용**: 별도의 가상 환경 관리 없이 실행

### Python 버전을 써야 할 때
- **가장 빠른 처리가 필요할 때**: 13.1배 더 빠름
- **대량 이미지 처리**: 성능 차이 큼
- **스마트 크롭 필요**: 얼굴/몸통 감지 지원
- **다양한 이미지 방향**: 세로/가로/정방형 자동 처리
- **일반적인 사용**: 대부분의 경우

### Go 버전을 써야 할 때
- **단일 바이너리 배포**: 의존성 없이 실행 가능
- **크로스 플랫폼**: Linux, macOS, Windows 지원
- **Shell보다 빠름**: 6.4배 더 빠름
- **메모리 효율성**: 낮은 메모리 사용량
- **세로형 이미지 전용**: 스마트 크롭 미지원

### Shell 버전을 써야 할 때
- **간단한 설치를 원할 때**: ImageMagick만 있으면 됨
- **수정이 자주 필요할 때**: Bash 스크립트 쉬운 편집
- **설치 간편성**: 추가 의존성 없음
- **세로형 이미지 전용**: 스마트 크롭 미지원

## 성능 비교

5개 이미지 처리 기준 (평균 8684x11467 픽셀)

| 버전 | 총 시간 | 평균/파일 | Python 대비 | Shell 대비 |
|------|---------|-----------|-----------|-----------|
| Python | 3.940초 | 0.788초 | 기준 | 13.1배 더 빠름 |
| Go | 8.105초 | 1.621초 | 2.1배 느림 | 6.4배 더 빠름 |
| Shell | 51.663초 | 10.333초 | 13.1배 느림 | 기준 |

**결론**: Python > Go > Shell (성능 순위)

## 검증 기록

### 2025-01-17 검증 (Go 버전 추가)

**테스트 이미지**: 5개 세로형 이미지 (ariel-introduction-04, 24, 26, 28, 29)
- 평균 크기: 8684x11467 픽셀
- 5개 모두 3840x2160으로 정확하게 변환됨
- 각 버전 2회 실행 후 평균 측정

**성능 측정 결과**:
||| 버전 | 1차 | 2차 | 평균 | 평균/파일 |
|||------|---------|---------|---------|-----------|
||| Python | 3.902초 | 3.977초 | 3.940초 | 0.788초 |
||| Go | 8.099초 | 8.110초 | 8.105초 | 1.621초 |
||| Shell | 51.626초 | 51.700초 | 51.663초 | 10.333초 |

**결론**:
- Python이 가장 빠름 (기준)
- Go는 Python보다 2.1배 느리지만 Shell보다 6.4배 빠름
- Shell이 가장 느림 (Python 대비 13.1배 느림)

## 자주 묻는 질문

### Q. 색감이 변한 것 같아요
A. ICC 프로필을 보존해서 원본 색감 그대로 유지됩니다.

### Q. "DecompressionBombWarning"이 떠요
A. PIL의 대용량 이미지 경고입니다. 무시해도 안전합니다.

### Q. 결과물이 어디에 생겨요?
A. Python은 `python/` 폴더, Go는 `go/` 폴더, Shell은 `shell/` 폴더에 저장됩니다.

### Q. 해상도를 바꾸고 싶어요
A. 스크립트 내의 `target_width`와 `target_height` 값을 수정하세요.

### Q. 가로형 이미지도 처리되나요?
A. 네, 스마트 크롭 기능으로 얼굴/몸통을 감지하여 최적의 크롭을 적용합니다.

### Q. 정방형 이미지는 처리되나요?
A. 자동으로 건너뜁니다. 16:9 변환 시 자르는 부분이 많아 품질 저하 예상됩니다.

### Q. 스마트 크롭은 언제 사용되나요?
A. 가로형 이미지에서 자동으로 적용됩니다. 얼굴/몸통 감지 후 3단계 폴백 체인으로 최적 크롭을 찾습니다.

## 라이선스

개인 프로젝트로 사용됩니다.

## 문제 신고

버그나 개선 제안은 환영합니다.
