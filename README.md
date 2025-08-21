# URL 파라미터 사용 안내서

## 개요
이 문서는 `https://github.com/boramahn/reportgen/static` 사용법을 설명합니다. 
이하 파리미터를 조합하여 [짧은 url제공하는 서비스](https://tinyurl.com/)를 이용해 배포합니다.

## 필수 파라미터 
### api (API 서버 주소) (필수)
- **설명**: 데이터를 가져올 API 서버의 주소 
- **예시값**: `my.k3s.url:8000`

## 편의 파라미터
### 웹페이지 수정시
webTitle 웹 페이지 제목 수정
webSubTitle 웹 페이지 제목 수정

### PDF 생성시
pdfTitle PDF 내용 중 상단 제목 수정
reviewerName 

## 사용 예시

### 기본 
```
http://localhost:8080/?api=my.k3s.url:8000
```

### 전체 파라미터 포함
```
http://localhost:8080/?api=my.k3s.url:8000&reportTitle=방학기록&reportSubTitle=6학년3반&pdfTitle=방학기록&reviewerName=한생님 선생님
``
