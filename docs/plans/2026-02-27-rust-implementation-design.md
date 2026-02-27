# Rust Implementation Design

**날짜**: 2026-02-27
**버전**: 1.0.0
**작성자**: AI (crong)

## 개요

Blossoming 프로젝트의 Rust 구현입니다. Python/Go/Shell 버전과 동일한 기능을 제공하면서 **최고 성능**과 **FFI 학습**을 목표로 합니다.

### 목표

1. **성능**: Python과 비슷하거나 약간 빠른 처리 속도 (~3-4초/5이미지)
2. **학습**: OpenCV C++ 라이브러리와 Rust FFI 연동 경험
3. **배포**: 소스 코드와 미리 빌드된 바이너리 모두 제공

---

## 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                         │
│                  (main.rs, clap)                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              ImageProcessor (Core Logic)                    │
│                  image crate (순수 Rust)                    │
├─────────────────────────────────────────────────────────────┤
│  • remove_watermark()    : Gaussian Blur                    │
│  • trim_margins()        : Fuzz-based edge detection        │
│  • resize()              : Lanczos3 resampling              │
│  • extend_aspect_ratio() : Blur expansion                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
┌───────────────▼─────────┐  ┌───────▼──────────────────────┐
│  Orientation Detection   │  │   SmartCrop (FFI)           │
│   (image crate)          │  │   (opencv crate)            │
├──────────────────────────┤  ├──────────────────────────────┤
│ • detect_orientation()   │  │ • detect_faces()            │
│ • Portrait/Landscape/    │  │ • detect_upper_body()       │
│   Square classification  │  │ • center_crop()             │
└──────────────────────────┘  └──────────────────────────────┘
```

### 책임 분리

| 모듈 | 라이브러리 | 역할 |
|------|-----------|------|
| `cli` | `clap` | 인자 파싱, 출력 폴더 관리 |
| `processor` | `image` | 워터마크 제거, 여백 제거, 리사이즈, 확장 |
| `orientation` | `image` | 이미지 방향 감지 |
| `smart_crop` | `opencv` | 얼굴/몸통 감지, 스마트 크롭 (FFI) |
| `error` | `thiserror` | 에러 타입 정의 |

### 의존성 크레이트

```toml
[dependencies]
clap = { version = "4.5", features = ["derive"] }
image = "0.25"
opencv = { version = "0.92", features = ["opencv-4"] }
thiserror = "2.0"
rayon = "1.10"

[dev-dependencies]
criterion = "0.5"
tempfile = "3.14"
```

---

## 데이터 흐름

### 전체 처리 플로우

```
입력 경로
  │
  ▼
이미지 파일 수집 (.jpg, .jpeg, .png, .bmp, .tiff, .tif)
  │
  ▼
병렬 처리 (rayon::par_iter)
  │
  ▼
┌─────────────────────────────────────────────┐
│ 개별 이미지 처리 (per-image pipeline)      │
├─────────────────────────────────────────────┤
│                                             │
│ 1. 이미지 로드 (ICC 프로필 보존)           │
│ 2. 방향 감지                                │
│    ├─ 세로형 → 워터마크→여백→리사이즈→확장 │
│    ├─ 가로형 → 스마트 크롭→리사이즈         │
│    └─ 정방형 → 건너뜀                      │
│ 3. 결과 저장 (quality: 95, ICC 보존)       │
│                                             │
└─────────────────────────────────────────────┘
  │
  ▼
진행률 표시 및 결과 요약
```

### 세로형 처리

```
입력 이미지
  │
  ▼
워터마크 제거 (하단 좌측 23% x 4%, Gaussian Blur radius=20)
  │
  ▼
여백 제거 (5% fuzz 기반 엣지 감지)
  │
  ▼
리사이즈 (높이 2160px 기준, Lanczos3)
  │
  ▼
16:9 확장 (좌우 1% 엣지, Blur radius=50)
  │
  ▼
출력 (3840x2160)
```

### 가로형 스마트 크롭

```
입력 이미지
  │
  ▼
OpenCV Mat 변환
  │
  ▼
Step 1: 얼굴 감지 (CascadeClassifier) → 실패 시 Step 2
  │
  ▼
Step 2: 몸통 감지 (HOGDetector) → 실패 시 Step 3
  │
  ▼
Step 3: 중앙 크롭 (폴백)
  │
  ▼
리사이즈 (너비 3840px 기준)
  │
  ▼
출력 (3840x2160)
```

---

## 컴포넌트 상세 설계

### 1. CLI 모듈 (`src/cli.rs`)

```rust
pub struct Config {
    pub input: PathBuf,
    pub output_dir: PathBuf,
    pub target_width: u32,
    pub target_height: u32,
    pub parallel: usize,
}

impl Config {
    pub fn from_args() -> Result<Self>;
    pub fn validate(&self) -> Result<()>;
}
```

### 2. Processor 모듈 (`src/processor.rs`)

```rust
pub struct ImageProcessor {
    config: ProcessorConfig,
}

impl ImageProcessor {
    pub fn remove_watermark(&self, img: &mut DynamicImage) -> Result<()>;
    pub fn trim_margins(&self, img: &mut DynamicImage) -> Result<()>;
    pub fn resize(&self, img: &mut DynamicImage) -> Result<()>;
    pub fn extend_aspect_ratio(&self, img: &mut DynamicImage) -> Result<()>;
}
```

### 3. Orientation 모듈 (`src/orientation.rs`)

```rust
pub enum Orientation {
    Portrait,
    Landscape,
    Square,
}

pub fn detect_orientation(width: u32, height: u32) -> Orientation;
```

### 4. SmartCrop 모듈 (`src/smart_crop.rs`)

```rust
pub struct SmartCropper {
    face_cascade: opencv::objdetect::CascadeClassifier,
    hog_detector: opencv::dnn::Net,
}

impl SmartCropper {
    pub fn smart_crop_landscape(&self, img: &Mat) -> Result<Mat>;
    fn try_face_detection(&self, img: &Mat) -> Result<Option<Mat>>;
    fn try_body_detection(&self, img: &Mat) -> Result<Option<Mat>>;
}
```

### 5. Error 모듈 (`src/error.rs`)

```rust
#[derive(Error, Debug)]
pub enum BlossomError {
    #[error("이미지 로드 실패: {path}")]
    ImageLoad { path: PathBuf, #[source] image::ImageError },

    #[error("OpenCV 오류: {0}")]
    OpenCV(#[from] opencv::Error),

    #[error("이미지 처리 실패: {0}")]
    Processing(String),

    #[error("정방형 이미지는 건너뜁니다: {0}")]
    SquareSkipped(PathBuf),
}

pub type Result<T> = std::result::Result<T, BlossomError>;
```

---

## 에러 처리

### 에러 처리 전략

- 개별 이미지 처리 실패 시 전체 중단하지 않고 계속 진행
- 최종 요약에서 성공/실패 카운트 표시
- 정방형 이미지는 에러로 처리하지만 복구 가능한 건너뜀으로 취급

### 에러 타입 계층

| 카테고리 | 에러 타입 | 복구 가능 여부 |
|----------|-----------|----------------|
| 이미지 로드 | `ImageLoad` | X (해당 파일만 스킵) |
| OpenCV | `OpenCVInit`, `CascadeLoadFailed` | X (치명적) |
| 처리 | `Processing` | X (해당 파일만 스킵) |
| 정방형 | `SquareSkipped` | O (의도된 건너뜀) |

---

## 테스트 전략

### 테스트 계층

```
tests/
├── integration/
│   └── full_pipeline_test.rs
├── unit/
│   ├── orientation_test.rs
│   ├── processor_test.rs
│   └── smart_crop_test.rs
└── fixtures/
    ├── portrait_sample.jpg
    ├── landscape_sample.jpg
    └── square_sample.jpg
```

### 테스트 실행

```bash
# 유닛 테스트
cargo test --lib

# 통합 테스트
cargo test --test integration

# 벤치마크
cargo bench

# 커버리지
cargo tarpaulin --out Html
```

---

## 빌드 및 배포

### 프로젝트 구조

```
widen_gracefully/
├── Cargo.toml
├── build.rs
├── src/
│   ├── main.rs
│   ├── cli.rs
│   ├── processor.rs
│   ├── orientation.rs
│   ├── smart_crop.rs
│   └── error.rs
├── tests/
└── docs/
    └── BUILD.md
```

### 빌드 설정

```toml
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
panic = "abort"
```

### GitHub Actions CI/CD

- 태그 푸시 시 자동으로 Linux/macOS/Windows 바이너리 빌드
- GitHub Releases에 자동 업로드

### 바이너리 크기

- 동적 링크: ~3MB
- 정적 링크: ~150-200MB (OpenCV 포함)

---

## 성능 목표

| 버전 | 5이미지 처리 시간 | 목표 |
|------|------------------|------|
| Python | 3.94초 | 기준 |
| Go | 8.11초 | - |
| **Rust** | **~3-4초** | **Python 대비 경쟁력** |

---

## 구현 방식: 혼합 (방식 3)

### 구성

- **스마트 크롭**: `opencv` crate (FFI)
- **나머지 처리**: `image` crate (순수 Rust)

### 이유

1. **학습**: FFI + 순수 Rust 두 영역 모두 경험
2. **성능**: 단순 작업은 순수 Rust가 더 빠름
3. **실용성**: 실제 Rust 프로젝트 일반적 패턴
4. **단계적 개발**: 스마트 크롭 제외하고 먼저 동작 가능

---

## 다음 단계

1. **Writing Plans**: 구현 계획 작성
2. **개발**: 단계별 구현
3. **테스트**: 단위/통합/성능 테스트
4. **배포**: GitHub Releases에 바이너리 게시
