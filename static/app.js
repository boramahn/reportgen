// app.js - 프론트엔드 JavaScript 로직


function getApiUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const apiParam = urlParams.get('api');
    


    if (apiParam) {
        // 쿼리 파라미터가 있으면 사용
        // http:// 또는 https://가 없으면 추가
        if (!apiParam.startsWith('http://') && !apiParam.startsWith('https://')) {
            return `https://${apiParam}`;
        }
        return apiParam;
    }
    
    // 기본값: localhost:8000
    return 'http://localhost:8000';
}

// API 엔드포인트 설정
const API_URL = getApiUrl();
console.log('API Server URL:', API_URL);

// DOM 요소 캐싱
const elements = {
    form: document.getElementById('reportForm'),
    fileInput: document.getElementById('image'),
    fileLabel: document.getElementById('fileLabel'),
    submitBtn: document.getElementById('submitBtn'),
    loading: document.getElementById('loading'),
    successMessage: document.getElementById('successMessage'),
    errorMessage: document.getElementById('errorMessage')
};

// 파일 선택 이벤트 처리
elements.fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        const fileName = e.target.files[0].name;
        const fileSize = (e.target.files[0].size / 1024 / 1024).toFixed(2);
        
        // 파일 크기 체크
        if (fileSize > 10) {
            showError('파일 크기는 10MB를 초과할 수 없습니다.');
            e.target.value = '';
            elements.fileLabel.textContent = '클릭하여 이미지 선택 또는 드래그 앤 드롭';
            elements.fileLabel.classList.remove('file-selected');
            return;
        }
        
        elements.fileLabel.textContent = `선택된 파일: ${fileName} (${fileSize}MB)`;
        elements.fileLabel.classList.add('file-selected');
    } else {
        elements.fileLabel.textContent = '클릭하여 이미지 선택 또는 드래그 앤 드롭';
        elements.fileLabel.classList.remove('file-selected');
    }
});

// 드래그 앤 드롭 이벤트 처리
const dragEvents = ['dragenter', 'dragover', 'dragleave', 'drop'];

dragEvents.forEach(eventName => {
    elements.fileLabel.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    elements.fileLabel.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    elements.fileLabel.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    elements.fileLabel.style.background = '#e7f1ff';
    elements.fileLabel.style.borderColor = '#667eea';
}

function unhighlight(e) {
    elements.fileLabel.style.background = '#f8f9fa';
    elements.fileLabel.style.borderColor = '#dee2e6';
}

elements.fileLabel.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const file = files[0];
        
        // 이미지 파일 체크
        if (!file.type.startsWith('image/')) {
            showError('이미지 파일만 업로드 가능합니다.');
            return;
        }
        
        // 파일 크기 체크
        const fileSize = (file.size / 1024 / 1024).toFixed(2);
        if (fileSize > 10) {
            showError('파일 크기는 10MB를 초과할 수 없습니다.');
            return;
        }
        
        elements.fileInput.files = files;
        elements.fileLabel.textContent = `선택된 파일: ${file.name} (${fileSize}MB)`;
        elements.fileLabel.classList.add('file-selected');
    }
}

// 폼 제출 처리
elements.form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // UI 상태 변경
    hideMessages();
    showLoading(true);
    elements.submitBtn.disabled = true;
    
    
    const formData = new FormData();
    formData.append('committee_name', document.getElementById('committeeName').value);
    formData.append('datetime_location', document.getElementById('datetimeLocation').value);
    formData.append('organizer', document.getElementById('organizer').value);
    formData.append('participants', document.getElementById('participants').value);
    formData.append('activity_content', document.getElementById('activityContent').value);
    formData.append('pdf_title',  document.getElementById('pdfTitle').value);
    formData.append('reviewer_name', document.getElementById('reviewerName').value);
    
    // 필수 필드 값 검증
    const requiredFields = {
        'committee_name': document.getElementById('committeeName').value,
        'datetime_location': document.getElementById('datetimeLocation').value,
        'organizer': document.getElementById('organizer').value,
        'participants': document.getElementById('participants').value,
        'activity_content': document.getElementById('activityContent').value,
        // 'reviewer_name': document.getElementById('reviewerName').value 
    };


    // FormData 내용 확인을 위한 로깅 추가
    for (let pair of formData.entries()) {
        console.log(pair[0] + ': ' + pair[1]);
    }
    
    
    const imageFile = elements.fileInput.files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    try {
        // API 호출
        const response = await fetch(`${API_URL}/generate-pdf`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'PDF 생성 실패');
        }
        
        // PDF 다운로드
        const blob = await response.blob();
        downloadPDF(blob);
        
        // 성공 메시지 표시
        showSuccess();
        
        // 폼 초기화
        setTimeout(() => {
            resetForm();
        }, 3000);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'PDF 생성 중 오류가 발생했습니다.');
    } finally {
        showLoading(false);
        elements.submitBtn.disabled = false;
    }
});

// PDF 다운로드 함수
function downloadPDF(blob) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${new Date().getTime()}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// UI 헬퍼 함수들
function showLoading(show) {
    if (show) {
        elements.loading.classList.add('active');
    } else {
        elements.loading.classList.remove('active');
    }
}

function showSuccess() {
    elements.successMessage.style.display = 'block';
    setTimeout(() => {
        elements.successMessage.style.display = 'none';
    }, 3000);
}

function showError(message) {
    const errorElement = elements.errorMessage;
    errorElement.textContent = `❌ ${message}`;
    errorElement.style.display = 'block';
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

function hideMessages() {
    elements.successMessage.style.display = 'none';
    elements.errorMessage.style.display = 'none';
}

function resetForm() {
    elements.form.reset();
    elements.fileLabel.textContent = '클릭하여 이미지 선택 또는 드래그 앤 드롭';
    elements.fileLabel.classList.remove('file-selected');
    hideMessages();
}

// 입력 필드 유효성 검사
document.getElementById('committeeName').addEventListener('input', function(e) {
    if (e.target.value.length > 50) {
        e.target.value = e.target.value.substring(0, 50);
    }
});

document.getElementById('participants').addEventListener('input', function(e) {
    if (e.target.value.length > 100) {
        e.target.value = e.target.value.substring(0, 100);
    }
});

document.getElementById('activityContent').addEventListener('input', function(e) {
    if (e.target.value.length > 2000) {
        e.target.value = e.target.value.substring(0, 2000);
    }
});

// 페이지 로드 시 API 상태 확인
window.addEventListener('DOMContentLoaded', async function() {
    const urlParams = new URLSearchParams(window.location.search);
    const committeeName = urlParams.get('committeeName');
    const organizer = urlParams.get('organizer');
    const participants = urlParams.get('participants');
    // const webTitle = urlParams.get('webTitle');
    const webSubTitle = urlParams.get('webSubTitle');
    const webTitle = urlParams.get('webTitle') || urlParams.get('title');


    const paramPdfTitle = urlParams.get('pdfTitle');
    const paramReviewerName = urlParams.get('reviewerName');

    // pdf 제목 업데이트
    if (paramPdfTitle) {
        const decodedPdfTitle = decodeURIComponent(paramPdfTitle);
        const pefTitleElement = document.getElementById('pdfTitle');
        pefTitleElement.value = decodedPdfTitle;
    }
    // 검수자 업데이트
    if (paramReviewerName) {
        const decodedReviewerName = decodeURIComponent(paramReviewerName);
        const reviewerNameElement = document.getElementById('reviewerName');
        reviewerNameElement.value = decodedReviewerName;
    }
    // 부제목 업데이트
    if (webSubTitle) {
        const decodedSubTitle = decodeURIComponent(webSubTitle);
        const subTitleElement = document.getElementById('webSubTitle');
        subTitleElement.textContent = decodedSubTitle;
    }

    // 제목 업데이트
    if (webTitle) {
        const decodedTitle = decodeURIComponent(webTitle);
        const titleElement = document.getElementById('webTitle');
        titleElement.textContent = decodedTitle;

        // 이모지가 포함되어 있지 않으면 추가
        const finalTitle = decodedTitle.startsWith('📄') ? decodedTitle : `📄 ${decodedTitle}`;
        titleElement.textContent = finalTitle;
    }
    // 부제목 업데이트
    if (webSubTitle) {
        const decodedSubTitle = decodeURIComponent(webSubTitle);
        const subTitleElement = document.getElementById('webSubTitle');
        subTitleElement.textContent = decodedSubTitle;
    }


    // committeeName 파라미터가 있으면 입력 필드에 설정
    if (committeeName) {
        document.getElementById('committeeName').value = committeeName;
        document.getElementById('organizer').value = organizer
        document.getElementById('participants').value = participants;    }
    try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) {
            console.warn('API 서버 연결 실패');
        } else {
            const data = await response.json();
            console.log('API 서버 연결 성공:', data);
        }
    } catch (error) {
        console.error('API 서버 연결 오류:', error);
        showError('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.');
    }
});
