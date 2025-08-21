# pdf_generator.py - PDF 생성 모듈
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import io
import os
import platform
from datetime import datetime
from typing import Optional
from PIL import ImageOps, Image as PILImage
from logger import get_logger
logger = get_logger()   

class PDFReportGenerator:
    """PDF 보고서 생성 클래스"""
    
    def __init__(self):
        """초기화 및 한글 폰트 설정"""
        self.font_name = self._register_korean_font()
        
    def _register_korean_font(self) -> str:
        """한글 폰트 등록"""
        current_dir = os.getcwd()
        print(f"현재 실행 디렉토리: {current_dir}")
        
        # 폰트 경로 목록 (TTC 파일 제외, TTF/OTF만 포함)
        font_paths = [
            # 현재 디렉토리의 fonts 폴더 (최우선)
            (os.path.join(current_dir, "fonts", "GowunBatang-Regular.ttf"), 'GowunBatang-Regular'),
            (os.path.join(current_dir, "fonts", "malgun.ttf"), 'MalgunGothic'),
            # Windows
            ("C:/Windows/Fonts/malgun.ttf", 'MalgunGothic'),
            ("C:/Windows/Fonts/malgunbd.ttf", 'MalgunGothicBold'),
            # Mac - TTF/OTF 파일만
            ("/Library/Fonts/NanumGothic.ttf", 'NanumGothic'),
            (os.path.expanduser("~/Library/Fonts/NanumGothic.ttf"), 'NanumGothic'),
            # Linux
            ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 'NanumGothic'),
        ]
        
        print("폰트 파일 검색 중...")
        
        for font_path, font_name in font_paths:
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                # TTC 파일 건너뛰기
                if expanded_path.endswith('.ttc'):
                    print(f"✗ TTC 파일 건너뛰기: {expanded_path}")
                    continue
                    
                try:
                    pdfmetrics.registerFont(TTFont(font_name, expanded_path))
                    print(f"✓ 폰트 등록 성공: {expanded_path} -> {font_name}")
                    return font_name
                except Exception as error:
                    print(f"✗ 폰트 등록 실패: {expanded_path}, 오류: {error}")
                    continue
        
        print("⚠ 한글 폰트를 찾을 수 없습니다. 기본 폰트 사용")
        return 'Helvetica'
        
    def _create_styles(self):
        """PDF 스타일 정의"""
        styles = getSampleStyleSheet()
        
        # 제목 스타일
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=self.font_name,
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # 날짜 스타일
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER
        )
        
        # 테이블 헤더 스타일
        header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=11,
            textColor=colors.HexColor('#ffffff'),
            alignment=TA_CENTER,
            leading=14
        )
        
        # 테이블 내용 스타일
        content_style = ParagraphStyle(
            'TableContent',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_LEFT,
            leading=14,
            leftIndent=10
        )

        # 테이블 내용 스타일
        sign_style = ParagraphStyle(
            'SignContent',
            parent=styles['Normal'],
            fontName=self.font_name,
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_RIGHT,
            spaceBefore=10
        )
        
        return {
            'title': title_style,
            'date': date_style,
            'header': header_style,
            'content': content_style,
            'sign': sign_style
        }
    

    def _compress_image(self, image_data: bytes, max_size_mb: float = 2.0) -> bytes:
        """이미지 압축"""
        try:
            # 이미지 열기
            img = PILImage.open(io.BytesIO(image_data))
            # EXIF 데이터 추출
            exif_data = None
            if 'exif' in img.info:
                exif_data = img.info['exif']
            # 현재 이미지 크기 (MB)
            current_size = len(image_data) / (1024 * 1024)
            
            # 이미지가 max_size보다 크면 압축
            if current_size > max_size_mb:
                # JPEG 품질 조정 (85는 좋은 품질과 압축률의 균형점)
                quality = 85
                
                # 압축된 이미지를 저장할 버퍼
                output_buffer = io.BytesIO()
                
                # PNG나 다른 형식의 이미지를 JPEG로 변환
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 이미지 저장 (압축)
                img.save(output_buffer, format='JPEG', quality=quality, optimize=True, exif=exif_data )
                compressed_data = output_buffer.getvalue()
                
                # 압축 후에도 크기가 큰 경우 품질을 더 낮춤
                while len(compressed_data) / (1024 * 1024) > max_size_mb and quality > 30:
                    quality -= 10
                    output_buffer = io.BytesIO()
                    img.save(output_buffer, format='JPEG', quality=quality, optimize=True, exif=exif_data )
                    compressed_data = output_buffer.getvalue()
                
                print(f"이미지 압축: {current_size:.1f}MB -> {len(compressed_data)/(1024*1024):.1f}MB (품질: {quality})")
                return compressed_data
                
            return image_data
            
        except Exception as error:
            print(f"이미지 압축 실패: {error}")
            return image_data

    
    def _process_image(self, image_data: bytes, styles: dict) -> any:
        """이미지 처리 및 크기 조정"""
        if not image_data:
            return Paragraph("첨부된 이미지가 없습니다", styles['content'])
        
        try:
            compressed_image = self._compress_image(image_data, max_size_mb=2.0)
            
            img_buffer = io.BytesIO(compressed_image)
            pil_img = PILImage.open(img_buffer)

            
            # 테이블 셀에 맞게 이미지 크기 조정
            max_width = 13.5 * cm
            max_height = 11.5 * cm
            
            img_width, img_height = pil_img.size
            aspect_ratio = img_width / img_height
            
            if aspect_ratio > max_width / max_height:
                new_width = max_width
                new_height = max_width / aspect_ratio
            else:
                new_height = max_height
                new_width = max_height * aspect_ratio
            
            # 크기가 작으면 적절히 확대
            if new_width < 8 * cm:
                scale = (8 * cm) / new_width
                new_width *= scale
                new_height *= scale
            
            img_buffer.seek(0)
            return Image(img_buffer, width=new_width, height=new_height)
            
        except Exception as error:
            print(f"이미지 처리 오류: {error}")
            return Paragraph("이미지 로드 실패", styles['content'])
    
    def _create_content(self, committee_name: str, datetime_location: str, 
                       organizer: str, participants: str, activity_content: str, reviewer_name: str = "", pdfTitle: str = "활동 기록",
                       image_data: Optional[bytes] = None) -> list:
        """PDF 내용 생성"""
        story = []
        styles = self._create_styles()
        
        # 제목
        story.append(Paragraph(pdfTitle, styles['title']))
        
        # # 작성일
        # current_date = datetime.now().strftime("%Y년 %m월 %d일")
        # story.append(Paragraph(f"작성일: {current_date}", styles['date']))
        # story.append(Spacer(1, 30))
        
        # 이미지 처리
        image_element = self._process_image(image_data, styles)
        
        # 2x6 테이블 데이터
        table_data = [
            [Paragraph("위원회명", styles['header']), 
             Paragraph(committee_name, styles['content'])],
            [Paragraph("일시/장소", styles['header']), 
             Paragraph(datetime_location, styles['content'])],
            [Paragraph("주최", styles['header']), 
             Paragraph(organizer, styles['content'])],
            [Paragraph("참석자", styles['header']), 
             Paragraph(participants, styles['content'])],
            [Paragraph("활동내용", styles['header']), 
             Paragraph(activity_content.replace('\n', '<br/>'), styles['content'])],
            [Paragraph("활동사진", styles['header']), 
             image_element]
        ]
        
        # 행 높이 설정
        row_heights = [1*cm, 1*cm, 1*cm, 1*cm, 7*cm, 11*cm]  # 이미지가 있는 행은 높이를 늘림   
        
        # 테이블 생성
        main_table = Table(
            table_data,
            colWidths=[3*cm, 14*cm],
            rowHeights=row_heights
        )
        

        # 테이블 스타일
        main_table.setStyle(TableStyle([
            # 테두리
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2c3e50')),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#95a5a6')),
            
            # 배경색
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#6c7a89')),# 이전: #34495e
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ffffff')),
            # 정렬
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 5), (1, 5), 'CENTER'),  # 이미지 셀 가로 중앙 정렬
            ('VALIGN', (1, 5), (1, 5), 'MIDDLE'), # 이미지 셀 세로 중앙 정렬
            
            # 이미지 셀의 패딩 조정
            ('TOPPADDING', (1, 5), (1, 5), 20),    # 이미지 위 여백
            ('BOTTOMPADDING', (1, 5), (1, 5), 20),  # 이미지 아래 여백
            ('LEFTPADDING', (1, 5), (1, 5), 0),     # 이미지 좌우 패딩 제거
            ('RIGHTPADDING', (1, 5), (1, 5), 0),
        ]))
        
        story.append(main_table)
        if reviewer_name != 'None' : 
            story.append(Paragraph("{} (인)".format(reviewer_name), styles['sign']))

        return story
    
    def create_report(self, committee_name: str, datetime_location: str,
                     organizer: str, participants: str, activity_content: str, reviewer_name: str = "", pdf_title: str = "활동 기록",  
                     image_data: Optional[bytes] = None) -> io.BytesIO:
        """PDF 보고서 생성 메인 메서드"""
        
        logger.info("PDF 보고서 생성 시작")
        logger.info(f"파라미터 정보:")
        logger.info(f"- 위원회명: {committee_name}")
        logger.info(f"- 일시/장소: {datetime_location}")
        logger.info(f"- 주최: {organizer}")
        logger.info(f"- 참석자: {participants}")
        logger.info(f"- 활동내용: {activity_content}")
        logger.info(f"- 검토자: {reviewer_name}")
        logger.info(f"- PDF 제목: {pdf_title}")
        logger.info(f"- 이미지 데이터 존재 여부: {image_data is not None}")
        buffer = io.BytesIO()
        
        # 문서 생성
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=3*cm,
            title=pdf_title
        )
        
        # 내용 생성 및 빌드
        content = self._create_content(
            committee_name, datetime_location, organizer,
            participants, activity_content, reviewer_name, pdf_title, image_data
        )
        
        doc.build(
            content,
            
        )
        
        buffer.seek(0)
        return buffer