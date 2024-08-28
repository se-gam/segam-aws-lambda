# 세감 람다 함수

<aside>
💡 세감에서 이용하는 세종대학교 내 여러 서비스에 접근하여 정보를 크롤링하거나, 예약/예약 취소를 하는 함수들입니다.

</aside>

## Auth

### Login

- 학번과 포털 비밀번호를 입력받아 기본 정보를 받아오는 API입니다.

## Ecampus

### AllCourseAttendance

- 학번과 포털 비밀번호를 입력받아 집현캠퍼스의 모든 출석 정보를 받아오는 API입니다.

## Studyroom

### Calander

- 스터디룸 혹은 SL의 room_id를 입력받아 예약 가능한 슬롯을 조회하는 API입니다.

### MyReservation

- 학번과 포털 비밀번호를 입력받아 내 스터디룸 예약 정보를 조회하는 API입니다.

### Reserve

- 학번과 포털 비밀번호, room_id, 예약 시간, 이용 시간을 입력받아 스터디룸을 예약하는 API입니다.

### Cancel

- 학번과 포털 비밀번호, booking_id, room_id를 입력받아 스터디룸 예약을 취소하는 API입니다.

### ValidateAvailability

- 학번과 포털 비밀번호, 동반 이용자명, 동반 이용자 학번, 예약 시간을 입력받아 스터디룸 예약이 가능한지 확인하는 API입니다.

## Godok

### Calander

- 고전독서시험의 현재 날짜로 부터 한달 동안의 예약 가능한 슬롯을 조회하는 API입니다.

### MyReservation

- 학번과 포털 비밀번호를 입력받아 내 고전독서 시험 예약 정보를 조회하는 API입니다.

### Reserve

- 학번과 포털 비밀번호, 책 정보, shInfoId를 입력받아 고전독서시험을 예약하는 API입니다.

### Cancel

- 학번과 포털 비밀번호, opAppInfoId를 입력받아 고전독서시험을 예약을 취소하는 API입니다.

### MyStatus

- 학번과 포털 비밀번호를 입력받아 내 고전독서 인증 현황을 조회하는 API입니다.
