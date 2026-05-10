# AGENTS.md

This document contains build, lint, and test commands along with code style guidelines for the Blossoming project.

## Build Commands

### Python
```bash
# Run Python script (recommended method)
python3 widen_gracefully.py <file_or_folder>

# Using uv (package manager)
uv run widen_gracefully.py <file_or_folder>

# Using uvx (single execution without installation)
uvx --from Pillow,numpy,opencv-python widen_gracefully.py <file_or_folder>
```

### Go
```bash
# Build Go binary
go build -o widen-gracefully-go widen_gracefully.go

# Run Go binary
./widen-gracefully-go <file_or_folder>

# Run directly with go run
go run widen_gracefully.go <file_or_folder>
```

### Shell
```bash
# Make shell script executable
chmod +x widen-gracefully-memory.sh

# Run shell script
./widen-gracefully-memory.sh <file_or_folder>
```

## Lint Commands

### Python
```bash
# Lint with ruff (if installed)
ruff check widen_gracefully.py

# Format with ruff
ruff format widen_gracefully.py

# Using uv to run ruff
uv run ruff check widen_gracefully.py
uv run ruff format widen_gracefully.py

# Check for type hints (optional)
uv run mypy widen_gracefully.py --ignore-missing-imports
```

### Go
```bash
# Format Go code
go fmt ./...

# Run go vet
go vet ./...

# Run gofmt
gofmt -w widen_gracefully.go
```

## Test Commands

### Running Tests
This project does not currently have automated tests. To test functionality:

```bash
# Test single image processing
python3 widen_gracefully.py test_image.jpg

# Verify output dimensions
identify python/test_image-4k.jpg

# Test with folder
python3 widen_gracefully.py /path/to/test_images
```

### Manual Test Checklist
- Vertical images: Check watermark removal, whitespace trimming, 16:9 conversion
- Horizontal images: Check smart crop, resize to 3840px width
- Square images: Should be skipped
- Output dimensions: Should be exactly 3840x2160
- Color preservation: Compare ICC profiles with original

## Code Style Guidelines

### Python

#### Imports
- Group imports: standard library first, then third-party
- Separate groups with blank line
- One import per line (except related modules)

```python
import os
import sys

from PIL import Image, ImageFilter, ImageChops
import numpy as np
import cv2
```

#### Formatting
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use f-strings for string formatting
- Prefer explicit is None checks over implicit truthiness

#### Naming Conventions
- Classes: PascalCase (e.g., `ImageConverter`)
- Functions/Methods: snake_case (e.g., `remove_watermark`)
- Constants: UPPER_SNAKE_CASE (e.g., `TARGET_WIDTH`)
- Private methods: prefix with underscore (e.g., `_crop_by_face`)
- Variables: snake_case

#### Type Hints
- Use type hints for function parameters and return values
- Import typing for complex types

```python
def remove_watermark(self, img: Image.Image) -> Image.Image:
    """Remove watermark region with blur processing (in-memory)"""
    pass
```

#### Error Handling
- Use try/except blocks for error handling
- Log errors with context
- Raise exceptions with descriptive messages

```python
try:
    with Image.open(input_path) as img:
        # processing code
        pass
except Exception as e:
    print(f"Error: {e}")
    raise
```

#### Documentation
- Use docstrings for all classes and public methods
- Docstrings describe what the function does, not how

```python
def remove_watermark(self, img):
    """워터마크 영역 블러처리 (메모리 처리)"""
    pass
```

#### Comments
- Use Korean for comments (matching existing codebase)
- Add inline comments for complex logic
- Avoid obvious comments

### Go

#### Imports
- Group imports: standard library first, then third-party
- Use blank line between groups

```go
import (
    "fmt"
    "os"

    "github.com/disintegration/imaging"
)
```

#### Formatting
- Use `gofmt` for formatting (standard Go formatting)
- Use tabs for indentation
- Maximum line length: 100 characters

#### Naming Conventions
- Packages: lowercase single words
- Exported functions/types: PascalCase (e.g., `ImageConverter`, `ProcessImage`)
- Private functions/types: camelCase (e.g., `removeWatermark`)
- Constants: PascalCase if exported, camelCase if private
- Interfaces: PascalCase with -er suffix (e.g., `Reader`, `Writer`)

#### Error Handling
- Always handle errors explicitly
- Use `fmt.Errorf` for error wrapping with context

```go
if err != nil {
    return fmt.Errorf("failed to open file: %w", err)
}
```

#### Documentation
- Use Go doc comments (exported symbols)
- Comments start with the symbol name

```go
// ImageConverter 이미지 변환기
type ImageConverter struct {
    // fields
}

// NewImageConverter 새로운 이미지 변환기 생성
func NewImageConverter() *ImageConverter {
    return &ImageConverter{...}
}
```

### Shell

#### Formatting
- Use 4 spaces for indentation
- Quote variables to prevent word splitting
- Use `[[` for tests instead of `[`

#### Naming Conventions
- Functions: lowercase_with_underscores
- Constants: UPPERCASE_WITH_UNDERSCORES
- Variables: lowercase_with_underscores

#### Error Handling
- Check command exit codes
- Use `set -e` to exit on error
- Provide error messages

```bash
process_image() {
    local input_file="$1"
    if [ ! -f "$input_file" ]; then
        echo "Error: File not found: $input_file"
        exit 1
    fi
}
```

## Project-Specific Guidelines

### File Organization
- Python outputs go to `python/` directory
- Go outputs go to `go/` directory
- Shell outputs go to `shell/` directory
- Input files follow pattern: `ariel-introduction-{number}-10000px.jpg`
- Output files follow pattern: `ariel-introduction-{number}-4k.jpg`

### Configuration Constants
- Target resolution: 3840x2160 (16:9)
- JPEG quality: 98
- Watermark position: bottom-left (23% width, 4% height)
- Edge blur percentage: 1%
- Trim fuzz threshold: 5%

### Memory Management
- Python: Process entirely in memory (no temporary files)
- Shell: Minimize file I/O, clean up temporary files
- Go: Use efficient memory patterns, monitor goroutine usage

### Color Preservation
- Always preserve ICC profiles when processing images
- Never strip color profiles
- Use `quality=98` for JPEG output

### Smart Crop (Python Only)
- 3-stage fallback chain: face detection → body detection → center crop
- OpenCV Haar Cascade for face detection
- HOG Detector for body detection
- Background color-based hair top detection

## Commit Conventions

Use Conventional Commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `test:` - Test additions or changes

Example:
```
feat: add smart crop for horizontal images
```
