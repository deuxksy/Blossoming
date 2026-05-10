#!/usr/bin/env python3

import os
import sys
from PIL import Image, ImageFilter, ImageChops
import numpy as np
import cv2


class ImageConverter:
    def __init__(self):
        self.watermark_width_ratio = 0.23
        self.watermark_height_ratio = 0.04
        self.target_width = 3840
        self.target_height = 2160
        self.edge_percent = 1
        self.trim_fuzz = 5  # 5%
        self.quality = 98

    def detect_orientation(self, img):
        """이미지 방향 감지 (portrait/landscape/square)"""
        width, height = img.size
        if height > width:
            return "portrait"
        elif width > height:
            return "landscape"
        else:
            return "square"

    def remove_watermark(self, img):
        """워터마크 영역 블러처리 (메모리 처리)"""
        img_width, img_height = img.size

        watermark_width = int(img_width * self.watermark_width_ratio)
        watermark_height = int(img_height * self.watermark_height_ratio)
        watermark_y = img_height - watermark_height

        print(f"원본 크기: {img_width}x{img_height}")
        print(f"워터마크 영역: {watermark_width}x{watermark_height} (좌하단)")

        # 워터마크 영역 추출 및 블러처리
        watermark_region = img.crop((0, watermark_y, watermark_width, img_height))
        blurred_watermark = watermark_region.filter(ImageFilter.GaussianBlur(radius=20))

        # 원본 이미지에 블러처리된 워터마크 영역 합성
        img.paste(blurred_watermark, (0, watermark_y))

        return img

    def trim_whitespace(self, img):
        """여백 제거 (fuzz 기반, 메모리 처리)"""
        width, height = img.size

        # 이미지를 numpy 배열로 변환
        pixels = np.array(img)

        # 모서리 픽셀을 기준으로 배경색 결정 (상단 좌측 10x10 영역)
        background_color = np.mean(pixels[0:10, 0:10, :])

        # fuzz 퍼센트를 RGB 값으로 변환 (5% = 12.75/255)
        fuzz_threshold = 12.75

        # 상단 여백 감지
        top = 0
        for y in range(height):
            row_mean = np.mean(np.abs(pixels[y, :, :] - background_color))
            if row_mean > fuzz_threshold:  # 배경과 다른 색상 발견
                top = y
                break

        # 하단 여백 감지
        bottom = height
        for y in range(height - 1, -1, -1):
            row_mean = np.mean(np.abs(pixels[y, :, :] - background_color))
            if row_mean > fuzz_threshold:  # 배경과 다른 색상 발견
                bottom = y + 1
                break

        print(f"여백 제거: 상단 {top}px, 하단 {height - bottom}px")

        # 크롭 (새로운 이미지 객체 반환)
        trimmed_img = img.crop((0, top, width, bottom))

        return trimmed_img

    def resize_to_height(self, img):
        """높이를 target_height로 리사이즈 (메모리 처리)"""
        original_width, original_height = img.size

        new_width = int(original_width * (self.target_height / original_height))
        resized_img = img.resize((new_width, self.target_height), Image.LANCZOS)

        print(f"리사이즈 완료: {new_width}x{self.target_height}")
        return resized_img

    def crop_to_16_9_center(self, img):
        """중앙을 기준으로 16:9 비율로 크롭 (너비 유지)"""
        width, height = img.size

        target_height = int(width * 9 / 16)
        crop_y = (height - target_height) // 2

        print(f"16:9 크롭: {width}x{target_height}")
        print(f"크롭 위치: Y={crop_y}부터 {crop_y + target_height}까지")

        return img.crop((0, crop_y, width, crop_y + target_height))

    def resize_to_width(self, img):
        """넓이를 target_width로 리사이즈 (16:9 비율 유지)"""
        width, height = img.size

        scale_ratio = self.target_width / width
        new_height = int(height * scale_ratio)

        resized_img = img.resize((self.target_width, new_height), Image.LANCZOS)

        print(f"리사이즈 완료: {self.target_width}x{new_height}")
        return resized_img

    def _find_best_crop_y(self, edge_density, target_height):
        """엣지 밀도가 최대인 크롭 위치 탐색"""
        height = len(edge_density)
        best_y = 0
        max_density = 0

        for y in range(height - target_height + 1):
            window_density = np.sum(edge_density[y : y + target_height])
            if window_density > max_density:
                max_density = window_density
                best_y = y

        return best_y

    def crop_16_9_smart_edge(self, img):
        """엣지 감지 기반 스마트 크롭"""
        width, height = img.size

        # PIL 이미지 → OpenCV 배열
        img_array = np.array(img)

        # 그레이스케일 변환
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Canny 엣지 감지
        edges = cv2.Canny(gray, 50, 150)

        # Y축별 엣지 밀도 계산
        edge_density = np.sum(edges, axis=1)

        # 최적 크롭 위치 탐색
        target_height = int(width * 9 / 16)
        best_y = self._find_best_crop_y(edge_density, target_height)

        # PIL 이미지로 복원
        cropped = img.crop((0, best_y, width, best_y + target_height))

        print(f"엣지 감지 스마트 크롭: {width}x{target_height}")
        print(f"크롭 위치: Y={best_y}부터 {best_y + target_height}까지")

        return cropped

    def _load_face_cascade(self):
        """Haar Cascade 얼굴 감지 모델 로드"""
        if not hasattr(self, "face_cascade"):
            # OpenCV 내장 Haar Cascade 사용
            haar_path = cv2.data.haarcascades
            self.face_cascade = cv2.CascadeClassifier(
                f"{haar_path}/haarcascade_frontalface_default.xml"
            )
            if self.face_cascade.empty():
                raise RuntimeError("Haar Cascade 모델 로드 실패")

    def crop_16_9_smart_face_cv2(self, img):
        """OpenCV Haar Cascade 기반 얼굴 감지 스마트 크롭"""
        width, height = img.size

        # 모델 로드 (첫 번째만)
        if not hasattr(self, "face_cascade"):
            print("얼굴 감지 모델 로드 중...")
            self._load_face_cascade()
            print("모델 로드 완료")

        # PIL → OpenCV
        img_array = np.array(img)

        # 그레이스케일 변환
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # 얼굴 감지
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) > 0:
            # 첫 번째 얼굴 사용
            (x, y, w, h) = faces[0]

            # 얼굴 중심
            face_center_y = y + h // 2

            # 타겟 높이
            target_height = int(width * 9 / 16)

            # 얼굴이 중앙 상단 1/3 지점에 오도록 크롭
            crop_y = max(
                0, min(face_center_y - target_height // 3, height - target_height)
            )

            print(f"얼굴 감지됨 ({len(faces)}개), 크롭 Y={crop_y}")
        else:
            # 얼굴 없으면 중앙 크롭
            target_height = int(width * 9 / 16)
            crop_y = (height - target_height) // 2
            print("얼굴 감지되지 않음, 중앙 크롭 사용")

        cropped = img.crop((0, crop_y, width, crop_y + target_height))

        return cropped

    def _crop_by_face(self, img):
        """얼굴 감지 기준 크롭"""
        width, height = img.size
        target_height = int(width * 9 / 16)

        # 얼굴 감지
        if not hasattr(self, "face_cascade"):
            print("  - 얼굴 감지 모델 로드 중...")
            self._load_face_cascade()
            print("  - 모델 로드 완료")

        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        if len(faces) > 0:
            (x, y, w, h) = faces[0]

            # 머리카락 끝 감지 시도
            hair_top_y = self._detect_hair_top(gray, x + w // 2, y)

            if hair_top_y is not None:
                # 엣지 감지 성공
                crop_y = max(0, hair_top_y - int(h * 0.1))
                print(f"  - 머리카락 감지됨 (엣지 기반), Y={crop_y}")
            else:
                # 엣지 감지 실패 → 보수적 여유 (장발 기준)
                hair_margin = int(h * 1.5)
                crop_y = max(0, y - hair_margin)
                print(f"  - 머리카락 감지 실패, 보수적 여유 사용, Y={crop_y}")
        else:
            return None  # 얼굴 없음

        cropped = img.crop((0, crop_y, width, crop_y + target_height))

        return cropped

    def _crop_by_body(self, img):
        """몸통 감지 기준 크롭"""
        width, height = img.size
        target_height = int(width * 9 / 16)

        # HOG Detector 로드
        if not hasattr(self, "hog"):
            print("  - HOG Detector 로드 중...")
            self._load_hog_detector()
            print("  - HOG Detector 로드 완료")

        # PIL → OpenCV
        img_array = np.array(img)

        # 몸통 감지
        boxes, weights = self.hog.detectMultiScale(
            img_array, winStride=(8, 8), padding=(8, 8), scale=1.05
        )

        if len(boxes) > 0:
            # 가장 상단 박스 선택
            top_body = min(boxes, key=lambda b: b[1])
            (x, y, w, h) = top_body

            # 몸통 상단에서 위로 여유 (머리카락 추정)
            # 몸통 높이(h)에서 머리 비율(20%) 추정
            head_estimate = int(h * 0.2)
            crop_y = max(0, y - head_estimate)

            print(f"  - 몸통 감지됨, 상단 Y={y}, 머리 추정={head_estimate}")
            print(f"  - 크롭 Y={crop_y}")

            cropped = img.crop((0, crop_y, width, crop_y + target_height))

            return cropped
        else:
            return None  # 몸통 없음

    def _crop_by_center(self, img):
        """중앙 기준 크롭"""
        width, height = img.size
        target_height = int(width * 9 / 16)

        crop_y = (height - target_height) // 2

        print(f"  - 중앙 크롭, Y={crop_y}")

        cropped = img.crop((0, crop_y, width, crop_y + target_height))

        return cropped

    def crop_16_9_smart_hybrid_v2(self, img):
        """3단계 폴백 스마트 크롭 (얼굴 → 몸통 → 중앙)"""
        width, height = img.size
        target_height = int(width * 9 / 16)

        print(f"하이브리드 스마트 크롭 v2: {width}x{target_height}")

        # 1차: 얼굴 감지 시도
        try:
            print("Step 1: 얼굴 감지 시도...")
            cropped = self._crop_by_face(img)
            if cropped is not None:
                return cropped
        except Exception as e:
            print(f"얼굴 감지 실패: {e}")

        # 2차: 몸통 감지 시도
        try:
            print("Step 2: 몸통 감지 시도...")
            cropped = self._crop_by_body(img)
            if cropped is not None:
                return cropped
        except Exception as e:
            print(f"몸통 감지 실패: {e}")

        # 3차: 중앙 크롭 (폴백)
        print("Step 3: 중앙 크롭으로 대체")
        return self._crop_by_center(img)

    def _detect_hair_top(self, gray, face_center_x, face_y):
        """배경색 기준 머리카락 끝 감지 (방안 3)"""

        # 배경색 결정 (얼굴 상단 위 20~50px, 좌우 100px)
        bg_region = gray[
            max(0, face_y - 50) : max(0, face_y - 20),
            max(0, face_center_x - 100) : min(gray.shape[1], face_center_x + 100),
        ]
        bg_color = int(np.mean(bg_region))

        # 스캔 범위: 얼굴 상단 위 100px까지
        max_scan_height = min(face_y + 50, face_y + 100)
        threshold = 30  # 배경색 차이 임계값

        # 다중 스캔 라인 (얼굴 중심, 좌측 50px, 우측 50px)
        scan_lines = [
            face_center_x,
            max(0, face_center_x - 50),
            min(gray.shape[1] - 1, face_center_x + 50),
        ]
        hair_tops = []

        # 각 스캔 라인에서 머리카락 끝 감지
        for scan_x in scan_lines:
            for y in range(face_y - 1, max(0, face_y - max_scan_height), -1):
                current_pixel = gray[y, scan_x]

                # 배경색과 다른 지점(머리카락 시작) 감지
                if abs(int(current_pixel) - bg_color) > threshold:
                    hair_tops.append(y + 1)
                    break

        # 여러 결과의 평균 사용
        if hair_tops:
            crop_y = max(0, int(np.mean(hair_tops)) - int(face_y * 0.05))
            return crop_y

        return None  # 감지 실패

    def _load_hog_detector(self):
        """HOG Person Detector 로드"""
        if not hasattr(self, "hog"):
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor.getDefaultPeopleDetector())
            self.hog = hog

    def convert_to_16x9(self, img):
        """16:9 변환 (조건부 처리: 좁은 이미지는 좌우 블러 확장, 넓은 이미지는 중앙 크롭)"""
        current_width, current_height = img.size

        print(f"현재 크기: {current_width}x{current_height}")

        # 높이 조정 (모든 경우에 필요)
        if current_height != self.target_height:
            img = img.resize((current_width, self.target_height), Image.LANCZOS)
            current_width, current_height = img.size

        # 조건부 분기
        if current_width < self.target_width:
            # === 좁은 이미지: 좌우 블러 확장 ===
            print("처리 방식: 좌우 블러 확장")

            edge_width = int(current_width * self.edge_percent / 100)
            blur_width = (self.target_width - current_width) // 2
            print(f"엣지 블러 폭: {edge_width}px, 확장 폭: {blur_width}px (좌우 각각)")

            # 좌측 엣지 추출 및 블러처리
            left_edge = img.crop((0, 0, edge_width, current_height))
            left_edge_resized = left_edge.resize(
                (blur_width, self.target_height), Image.LANCZOS
            )
            left_blurred = left_edge_resized.filter(ImageFilter.GaussianBlur(radius=50))

            # 우측 엣지 추출 및 블러처리
            right_edge = img.crop(
                (current_width - edge_width, 0, current_width, current_height)
            )
            right_edge_resized = right_edge.resize(
                (blur_width, self.target_height), Image.LANCZOS
            )
            right_blurred = right_edge_resized.filter(
                ImageFilter.GaussianBlur(radius=50)
            )

            # 이미지 합성
            result = Image.new("RGB", (self.target_width, self.target_height))
            result.paste(left_blurred, (0, 0))
            result.paste(img, (blur_width, 0))
            result.paste(right_blurred, (blur_width + current_width, 0))

        elif current_width > self.target_width:
            # === 넓은 이미지: 중앙 크롭 ===
            print("처리 방식: 중앙 크롭")

            crop_x = (current_width - self.target_width) // 2
            print(f"크롭 위치: 좌측 {crop_x}px부터 {crop_x + self.target_width}px까지")

            result = img.crop(
                (crop_x, 0, crop_x + self.target_width, self.target_height)
            )

        else:
            # === 정확한 비율: 그대로 사용 ===
            print("처리 방식: 이미 정확한 16:9 비율")
            result = img

        return result

    def process_image(self, input_path):
        """전체 처리 프로세스 (메모리 처리)"""
        if not os.path.exists(input_path):
            print(f"파일이 존재하지 않습니다: {input_path}")
            return

        basename = os.path.basename(input_path)
        name_without_ext = os.path.splitext(basename)[0]
        output_name = name_without_ext.replace("-10000px", "") + "-4k.jpg"
        output_path = os.path.join("python", output_name)

        os.makedirs("python", exist_ok=True)

        print("=== 우아하게 넓히기 ===")
        print("")

        try:
            with Image.open(input_path) as img:
                icc_profile = img.info.get("icc_profile")

                # 이미지 방향 감지
                orientation = self.detect_orientation(img)
                print(f"이미지 방향: {orientation}")

                # 정방형: 건너뜀
                if orientation == "square":
                    print("정방형 이미지: 처리 건너뜀")
                    return

                if orientation == "portrait":
                    # 세로형: 기존 로직 유지
                    # Step 1: 워터마크 제거
                    print("=== Step 1: 워터마크 제거 ===")
                    img = self.remove_watermark(img)
                    print("")

                    # Step 2: 여백 제거 및 리사이즈
                    print("=== Step 2: 여백 제거 및 리사이즈 ===")
                    img = self.trim_whitespace(img)
                    img = self.resize_to_height(img)
                    print("")

                    # Step 3: 16:9 변환
                    print("=== Step 3: 16:9 변환 ===")
                    result_img = self.convert_to_16x9(img)
                    print("")

                elif orientation == "landscape":
                    # 가로형: 스마트 크롭 (워터마크/여백 제거 스킵)
                    print("=== 가로형 이미지 처리 (스마트 크롭) ===")

                    # Step 1: 하이브리드 스마트 크롭 (3단계 폴백)
                    print("Step 1: 하이브리드 스마트 크롭 (3단계 폴백)")
                    img = self.crop_16_9_smart_hybrid_v2(img)
                    print("")

                    # Step 2: 넓이 3840 리사이즈
                    print("Step 2: 넓이 3840 리사이즈")
                    img = self.resize_to_width(img)
                    result_img = img
                    print("")

                # 결과 저장 (마지막에만 파일 I/O)
                if icc_profile:
                    result_img.save(
                        output_path,
                        quality=self.quality,
                        subsampling=1,
                        icc_profile=icc_profile,
                    )
                else:
                    result_img.save(output_path, quality=self.quality, subsampling=1)

                result_size = result_img.size
                print("=== 완료! ===")
                print(
                    f"생성된 파일: python/{output_name} ({result_size[0]}x{result_size[1]})"
                )

        except Exception as e:
            print(f"오류 발생: {e}")
            raise


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 widen_gracefully.py <image_file_or_folder>")
        sys.exit(1)

    input_path = sys.argv[1]
    converter = ImageConverter()

    if os.path.isfile(input_path):
        converter.process_image(input_path)
    elif os.path.isdir(input_path):
        supported_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")
        processed = 0
        for root, _, files in os.walk(input_path):
            for filename in sorted(files):
                if filename.lower().endswith(supported_extensions):
                    filepath = os.path.join(root, filename)
                    print(f"\n{'=' * 60}")
                    print(f"Pro안cessing: {filename}")
                    print("=" * 60)
                    converter.process_image(filepath)
                    processed += 1
        print(f"\n총 {processed}개 이미지 처리 완료")
    else:
        print(f"오류: '{input_path}'은(는) 존재하지 않는 파일 또는 폴더입니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
