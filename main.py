# main.py - FastAPI 백엔드 서버
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from typing import Optional
import io
from PIL import Image as PILImage
from pdf_generator import PDFReportGenerator
from logger import get_logger
logger = get_logger()   

app = FastAPI(title="PDF Report Generator API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static 파일 서빙 (HTML, CSS, JS)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# PDF 생성기 인스턴스
pdf_generator = PDFReportGenerator()

@app.get("/")
async def read_root():
    """API 정보 반환"""
    return {
        "message": "PDF Report Generator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate-pdf": "PDF 생성",
            "GET /health": "서버 상태 확인"
        }
    }

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "font_status": pdf_generator.font_name
    }

@app.post("/generate-pdf")
async def generate_pdf(
    committee_name: str = Form(..., description="위원회명"),
    datetime_location: str = Form(..., description="일시/장소"),
    organizer: str = Form(..., description="주최"),
    participants: str = Form(..., description="참석자"),
    activity_content: str = Form(..., description="활동내용"),
    pdf_title: str = Form(..., description="pdf 상단 제목"),
    reviewer_name: str = Form(..., description="활동내용"),
    image: Optional[UploadFile] = File(None, description="활동사진")
):
    """
    PDF 보고서 생성 엔드포인트
    
    Parameters:
    - committee_name: 위원회 또는 조직명
    - datetime_location: 활동 일시 및 장소
    - organizer: 주최 부서 또는 담당자
    - participants: 참석자 명단
    - activity_content: 활동 내용 상세
    - pdf_title: PDF 상단 제목 (기본값: "모임 활동 기록")
    - reviewer_name: 검토자 이름 (기본값: "홍 길 동")
    - image: 활동 사진 (선택사항)
    
    Returns:
    - PDF 파일
    """
    try:
        logger.info("PDF 생성 요청 수신")   
        # 이미지 데이터 처리
        image_data = None
        if image and image.filename:
            # 파일 크기 체크 (10MB 제한)
            image_data = await image.read()
            if len(image_data) > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="파일 크기는 10MB를 초과할 수 없습니다.")
            
            # 이미지 유효성 검사
            try:
                img_buffer = io.BytesIO(image_data)
                PILImage.open(img_buffer)
            except Exception:
                raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다.")
        
        # PDF 생성
        pdf_buffer = pdf_generator.create_report(
            committee_name=committee_name,
            datetime_location=datetime_location,
            organizer=organizer,
            participants=participants,
            activity_content=activity_content,
            pdf_title=pdf_title,
            reviewer_name=reviewer_name,
            image_data=image_data
        )
        
        # 파일명 생성
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # PDF 파일을 임시로 저장
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        temp_path = os.path.join(temp_dir, filename)
        with open(temp_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # 파일 응답
        response = FileResponse(
            temp_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
        # 임시 파일 삭제 (응답 후)
        import threading
        import time
        def delete_file():
            time.sleep(10)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
        
        threading.Thread(target=delete_file, daemon=True).start()
        
        return response
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"PDF 생성 중 오류: {str(error)}" )
        raise HTTPException(status_code=500, detail=f"PDF 생성 중 오류가 발생했습니다: {str(error)}")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("\n" + "="*50)
    logger.info("PDF Report Generator Server")
    logger.info("="*50)
    logger.info(f"한글 폰트: {pdf_generator.font_name}")
    logger.info("서버 시작 중...")
    logger.info("\nAPI 문서: http://localhost:8000/docs")
    logger.info("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, workers=1)