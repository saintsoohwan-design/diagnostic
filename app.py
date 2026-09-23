# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import socket
import random
import time

app = FastAPI(title="국립특수교육원 기초학습능력 통합 스크리닝 시스템 v8 (Reading, Writing, Math 25-Min Integrated)")

# 검사 데이터 정의 (국어 읽기/쓰기 & 수학 통합)
TEST_CONTENT = {
    "phoneme": {
        "title": "I. 국어 - 음운 처리",
        "subtests": {
            "ran_object": {
                "name": "1. 빠른 이름대기 (RAN-사물 1분)",
                "stop_rule": 99,
                "type": "ran",
                "questions": [
                    {
                        "q": "⚽️ 🍚 🐎 🥛 ✋ 🚗 🐶 🍎 🚲 👟", 
                        "a": "축구공, 밥, 말, 컵, 손, 자동차, 강아지, 사과, 자전거, 신발", 
                        "guide": "1분간 아동이 왼쪽에서 오른쪽으로 빠르게 그림 이름을 대도록 하세요. 교사는 오독/빠뜨린 항목만 체크합니다."
                    }
                ]
            },
            "blending": {
                "name": "2. 음절 합성 및 탈락",
                "stop_rule": 3,
                "questions": [
                    {"q": "/편/ + /지/", "a": "편지", "guide": "선생님: '/편/ 소리와 /지/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/토/ + /끼/", "a": "토끼", "guide": "선생님: '/토/ 소리와 /끼/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/비/ + /둘/ + /기/", "a": "비둘기", "guide": "선생님: '/비/ 소리와 /둘/ 소리와 /기/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "'산길'에서 '산'을 빼면?", "a": "길", "guide": "'산길'에서 '산' 소리를 빼고 남은 소리를 말해보세요."}
                ]
            }
        }
    },
    "word": {
        "title": "II. 국어 - 글자·단어 인지",
        "subtests": {
            "letter": {
                "name": "1. 낱글자 인지",
                "stop_rule": 3,
                "questions": [
                    {"q": "ㄹ", "a": "리을", "guide": "이 낱글자의 이름은 무엇일까요?"},
                    {"q": "ㅂ", "a": "비읍", "guide": "이 낱글자의 이름은 무엇일까요?"},
                    {"q": "ㅆ", "a": "쌍시옷", "guide": "이 낱글자의 이름은 무엇일까요?"}
                ]
            },
            "word_rec": {
                "name": "2. 단어 인지 (규칙/불규칙)",
                "stop_rule": 3,
                "questions": [
                    {"q": "선물", "a": "선물", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "꽃", "a": "꼳", "guide": "이 단어를 정확한 소리로 읽어보세요."},
                    {"q": "국민", "a": "궁민", "guide": "이 단어를 정확한 소리로 읽어보세요."}
                ]
            }
        }
    },
    "reading_fluency": {
        "title": "III. 국어 - 읽기 유창성",
        "subtests": {
            "reading_flow": {
                "name": "1. 1분 글 읽기 유창성",
                "stop_rule": 99,
                "type": "text_flow",
                "questions": [
                    {
                        "q": "개는 사람이 집에서 기르는 동물 중에서 가장 오래된 동물입니다. 그래서 세계 어느 나라에서나 개를 기르는 모습을 볼 수 있습니다. 우리나라에서 옛날부터 기르던 개로는 진돗개, 삽살개, 풍산개가 있습니다...", 
                        "a": "분당 정확히 읽은 음절 수 채점", 
                        "guide": "아동이 1분 동안 소리 내어 글을 읽도록 하고 오독 수/어절을 채점하세요."
                    }
                ]
            }
        }
    },
    "vocab": {
        "title": "IV. 국어 - 어휘 및 이해",
        "subtests": {
            "vocab_test": {
                "name": "1. 어휘력 (반대말/유추/빈칸)",
                "stop_rule": 3,
                "questions": [
                    {"q": "더하다 <-> ( ? )", "a": "빼다", "guide": "'더하다'의 반대말은 무엇일까요?"},
                    {"q": "손 : 장갑 = 발 : ( ? )", "a": "양말 / 신발", "guide": "손에 장갑을 끼듯이 발에는 무엇을 신을까요?"},
                    {"q": "비가 오면 ( ? )을 씁니다.", "a": "우산", "guide": "문맥에 맞는 단어를 말해보세요."}
                ]
            },
            "comprehension": {
                "name": "2. 지문 독해 및 이해",
                "stop_rule": 3,
                "questions": [
                    {"q": "손을 머리 위로 드세요.", "a": "동작 수행", "guide": "아동이 문장을 읽고 그에 맞는 동작을 수행하게 하세요."},
                    {"q": "글의 중심 내용을 고르세요.", "a": "중심 내용 답안", "guide": "글을 읽고 핵심주제를 이야기해보세요."}
                ]
            }
        }
    },
    "writing": {
        "title": "V. 국어 - 쓰기 및 문법",
        "subtests": {
            "handwriting_spelling": {
                "name": "1. 글씨쓰기 & 철자하기",
                "stop_rule": 3,
                "questions": [
                    {"q": "학교 (받아쓰기)", "a": "학교", "guide": "선생님이 불러주는 단어를 바르게 써보세요: '학교'"},
                    {"q": "부억 (맞춤법 고치기)", "a": "부엌", "guide": "틀린 맞춤법을 올바르게 고쳐 써보세요: '부억'"}
                ]
            },
            "grammar_composition": {
                "name": "2. 문법 및 표현 (짧은 글짓기)",
                "stop_rule": 3,
                "questions": [
                    {"q": "주어-술어 호응 문장 완성", "a": "문장 구성", "guide": "'나는 내일 친구와 함께 ____.' 문장을 완성해 보세요."},
                    {"q": "높임법 고쳐 쓰기", "a": "할머니께서 진지를 드신다.", "guide": "'할머니가 밥을 먹는다'를 높임말로 바꿔보세요."}
                ]
            }
        }
    },
    "math_num": {
        "title": "VI. 수학 - 수와 연산",
        "subtests": {
            "basic_ops": {
                "name": "1. 수 개념 및 연산",
                "stop_rule": 3,
                "questions": [
                    {"q": "5 + 3 = ?", "a": "8", "guide": "덧셈 문제를 풀어보세요."},
                    {"q": "12 - 4 = ?", "a": "8", "guide": "뺄셈 문제를 풀어보세요."},
                    {"q": "1/4 + 2/4 = ?", "a": "3/4", "guide": "분수의 덧셈을 풀어보세요."}
                ]
            }
        }
    },
    "math_geo": {
        "title": "VII. 수학 - 도형 및 측정",
        "subtests": {
            "geo_measure": {
                "name": "1. 도형 및 측정",
                "stop_rule": 3,
                "questions": [
                    {"q": "🔺 이 모양의 이름은?", "a": "삼각형", "guide": "그림을 보고 도형의 이름을 말해보세요."},
                    {"q": "시계 읽기 (3시 30분)", "a": "3시 30분", "guide": "시계가 가리키는 시간을 읽어보세요."}
                ]
            }
        }
    },
    "math_pattern": {
        "title": "VIII. 수학 - 규칙성 및 자료·가능성",
        "subtests": {
            "pattern_data": {
                "name": "1. 규칙성 및 자료 표현",
                "stop_rule": 3,
                "questions": [
                    {"q": "2, 4, 6, ( ? ), 10", "a": "8", "guide": "빈칸에 들어갈 규칙적인 숫자를 말해보세요."},
                    {"q": "막대그래프 해석 (가장 많은 항목)", "a": "그래프 답안", "guide": "그래프에서 가장 높은 막대가 의미하는 항목을 말해보세요."}
                ]
            }
        }
    }
}

# 4대 대상군별 통합 스크리닝 프리셋 매핑
PRESET_MAPPING = {
    "1": {
        "name": "1. 초1 스크리닝 (기초 해독 & 수 개념)",
        "desc": "음운 처리, 낱글자 인지, 글씨쓰기, 10 이하 연산 스크리닝",
        "domains": [("phoneme", "ran_object"), ("phoneme", "blending"), ("word", "letter"), ("writing", "handwriting_spelling"), ("math_num", "basic_ops")]
    },
    "2": {
        "name": "2. 초3 발달지체 재심의 (결손 보완 분기)",
        "desc": "읽기 유창성, 어휘력, 쓰기 문법, 수 연산 및 도형 기초 스크리닝",
        "domains": [("reading_fluency", "reading_flow"), ("vocab", "vocab_test"), ("writing", "grammar_composition"), ("math_num", "basic_ops"), ("math_geo", "geo_measure")]
    },
    "3": {
        "name": "3. 중입 (교과 문해력 & 수학)",
        "desc": "지문 독해, 고급 어휘, 쓰기 표현, 분수 연산 및 규칙성 스크리닝",
        "domains": [("vocab", "comprehension"), ("vocab", "vocab_test"), ("writing", "grammar_composition"), ("math_num", "basic_ops"), ("math_pattern", "pattern_data")]
    },
    "4": {
        "name": "4. 고입 (~중3 전환기 기능적 평가)",
        "desc": "기능적 문해력, 추론 독해, 논리적 글쓰기, 생활 수학 스크리닝",
        "domains": [("vocab", "comprehension"), ("writing", "grammar_composition"), ("math_num", "basic_ops"), ("math_geo", "geo_measure"), ("math_pattern", "pattern_data")]
    }
}

# 다중 검사방(Room) 클래스
class RoomState:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.created_at = time.time()
        self.last_active = time.time()
        self.student_name = ""
        self.student_grade = ""
        self.preset_mode = ""
        self.current_question_idx = 0
        self.scores = {}
        self.stop_triggered = False
        self.consecutive_wrong = 0
        self.test_completed = False
        self.supplementary_recommended = []
        self.supplementary_active = False

    def touch(self):
        self.last_active = time.time()

    def get_current_domain_and_subtest(self):
        if not self.preset_mode or self.preset_mode not in PRESET_MAPPING:
            return None, None
        preset = PRESET_MAPPING[self.preset_mode]
        domains = preset["domains"]
        if self.current_question_idx >= len(domains):
            return None, None
        return domains[self.current_question_idx]

    def build_payload(self):
        self.touch()
        dom, sub = self.get_current_domain_and_subtest()
        current_q_data = None
        subtest_title = ""
        domain_title = ""
        is_ran_or_flow = False
        
        if dom and sub:
            domain_title = TEST_CONTENT[dom]["title"]
            subtest_data = TEST_CONTENT[dom]["subtests"][sub]
            subtest_title = subtest_data["name"]
            
            subtest_idx = 0
            if f"{dom}_{sub}" in self.scores:
                subtest_idx = len(self.scores[f"{dom}_{sub}"])
                
            if subtest_idx < len(subtest_data["questions"]):
                current_q_data = subtest_data["questions"][subtest_idx]
                if "type" in subtest_data and subtest_data["type"] in ["ran", "text_flow"]:
                    is_ran_or_flow = True
            else:
                current_q_data = {"q": "하위검사 완료", "a": "", "guide": "다음 영역으로 넘어가세요."}

        return {
            "room_id": self.room_id,
            "student_name": self.student_name,
            "student_grade": self.student_grade,
            "preset_name": PRESET_MAPPING.get(self.preset_mode, {}).get("name", ""),
            "domain_title": domain_title,
            "subtest_title": subtest_title,
            "current_question": current_q_data["q"] if current_q_data else "",
            "current_answer": current_q_data["a"] if current_q_data else "",
            "current_guide": current_q_data["guide"] if current_q_data else "",
            "stop_triggered": self.stop_triggered,
            "test_completed": self.test_completed,
            "is_ran_or_flow": is_ran_or_flow,
            "scores": self.scores,
            "supplementary_recommended": self.supplementary_recommended,
            "supplementary_active": self.supplementary_active
        }

    def advance_next_step(self):
        self.consecutive_wrong = 0
        self.current_question_idx += 1
        dom, sub = self.get_current_domain_and_subtest()
        if dom and sub:
            self.scores[f"{dom}_{sub}"] = []
        else:
            self.test_completed = True
            self.analyze_supplementary_recommendations()

    def analyze_supplementary_recommendations(self):
        korean_score_sum = 0
        korean_count = 0
        math_score_sum = 0
        math_count = 0

        for sub_key, scores in self.scores.items():
            if len(scores) > 0:
                pct = sum(scores) / len(scores)
                if sub_key.startswith("math"):
                    math_score_sum += pct
                    math_count += 1
                else:
                    korean_score_sum += pct
                    korean_count += 1

        if korean_count > 0 and (korean_score_sum / korean_count) < 0.8:
            self.supplementary_recommended.append("국어 음운/낱글자 보완 정밀검사")
            self.supplementary_recommended.append("국어 기초 철자/쓰기 보완검사")

        if math_count > 0 and (math_score_sum / math_count) < 0.8:
            self.supplementary_recommended.append("수학 연산 유창성 하향 보완검사")

# 글로벌 다중 검사방 저장소
ROOMS: Dict[str, RoomState] = {}

def get_or_create_room(room_id: Optional[str] = None) -> RoomState:
    if room_id and room_id in ROOMS:
        return ROOMS[room_id]
    
    for _ in range(100):
        new_pin = str(random.randint(1000, 9999))
        if new_pin not in ROOMS:
            ROOMS[new_pin] = RoomState(new_pin)
            return ROOMS[new_pin]
            
    fallback_pin = str(time.time_ns())[-4:]
    ROOMS[fallback_pin] = RoomState(fallback_pin)
    return ROOMS[fallback_pin]

# REST API Models & Endpoints
class StartRequest(BaseModel):
    room_id: str
    student_name: str
    student_grade: str
    preset_mode: str

class GradeRequest(BaseModel):
    room_id: str
    score: int

class ActionRequest(BaseModel):
    room_id: str

@app.post("/api/create_room")
def api_create_room():
    room = get_or_create_room()
    return {"room_id": room.room_id}

@app.get("/api/state")
def get_state(room: str):
    if not room or room not in ROOMS:
        return JSONResponse(status_code=404, content={"error": "invalid_room", "message": "존재하지 않거나 만료된 방 번호입니다."})
    room_obj = ROOMS[room]
    return JSONResponse(content=room_obj.build_payload())

@app.post("/api/start")
def api_start(req: StartRequest):
    room_obj = get_or_create_room(req.room_id)
    room_obj.student_name = req.student_name
    room_obj.student_grade = req.student_grade
    room_obj.preset_mode = req.preset_mode
    room_obj.current_question_idx = 0
    room_obj.scores = {}
    room_obj.stop_triggered = False
    room_obj.consecutive_wrong = 0
    room_obj.test_completed = False
    room_obj.supplementary_recommended = []
    room_obj.supplementary_active = False

    dom, sub = room_obj.get_current_domain_and_subtest()
    if dom and sub:
        room_obj.scores[f"{dom}_{sub}"] = []
    return {"status": "ok"}

@app.post("/api/grade")
def api_grade(req: GradeRequest):
    if req.room_id not in ROOMS:
        return JSONResponse(status_code=404, content={"error": "invalid_room"})
    room_obj = ROOMS[req.room_id]
    score = req.score
    dom, sub = room_obj.get_current_domain_and_subtest()
    
    if dom and sub:
        sub_key = f"{dom}_{sub}"
        if sub_key not in room_obj.scores:
            room_obj.scores[sub_key] = []
        
        room_obj.scores[sub_key].append(score)
        
        if score == 0:
            room_obj.consecutive_wrong += 1
        else:
            room_obj.consecutive_wrong = 0
            
        subtest_data = TEST_CONTENT[dom]["subtests"][sub]
        stop_threshold = subtest_data.get("stop_rule", 3)
        
        if room_obj.consecutive_wrong >= stop_threshold:
            room_obj.stop_triggered = True
            room_obj.consecutive_wrong = 0
        else:
            current_len = len(room_obj.scores[sub_key])
            total_q_len = len(subtest_data["questions"])
            if current_len >= total_q_len:
                room_obj.advance_next_step()
                
    return {"status": "ok"}

@app.post("/api/skip")
def api_skip(req: ActionRequest):
    if req.room_id in ROOMS:
        ROOMS[req.room_id].advance_next_step()
    return {"status": "ok"}

@app.post("/api/resume")
def api_resume(req: ActionRequest):
    if req.room_id in ROOMS:
        room_obj = ROOMS[req.room_id]
        room_obj.stop_triggered = False
        room_obj.advance_next_step()
    return {"status": "ok"}

@app.post("/api/supplementary")
def api_supplementary(req: ActionRequest):
    if req.room_id in ROOMS:
        room_obj = ROOMS[req.room_id]
        room_obj.supplementary_active = True
        room_obj.test_completed = False
        room_obj.stop_triggered = False
        room_obj.current_question_idx = 0
        
        supp_domains = []
        for rec_name in room_obj.supplementary_recommended:
            if "음운" in rec_name:
                supp_domains.append(("phoneme", "blending"))
                supp_domains.append(("word", "letter"))
            if "철자" in rec_name:
                supp_domains.append(("writing", "handwriting_spelling"))
            if "수학" in rec_name:
                supp_domains.append(("math_num", "basic_ops"))
        
        PRESET_MAPPING["supplementary"] = {
            "name": "보완 정밀 진단검사 모드",
            "domains": supp_domains
        }
        room_obj.preset_mode = "supplementary"
        room_obj.scores = {}
        room_obj.supplementary_recommended = []
        
        dom, sub = room_obj.get_current_domain_and_subtest()
        if dom and sub:
            room_obj.scores[f"{dom}_{sub}"] = []
    return {"status": "ok"}

@app.post("/api/reset")
def api_reset(req: ActionRequest):
    if req.room_id in ROOMS:
        room_obj = ROOMS[req.room_id]
        room_obj.student_name = ""
        room_obj.student_grade = ""
        room_obj.preset_mode = ""
        room_obj.scores = {}
        room_obj.stop_triggered = False
        room_obj.consecutive_wrong = 0
        room_obj.test_completed = False
        room_obj.supplementary_recommended = []
        room_obj.supplementary_active = False
    return {"status": "ok"}

# 교사용 UI HTML
TEACHER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>교사용 기초학습능력 통합 스크리닝 패널 v8</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans KR', sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; color: #333; }
        .header { background-color: #1e3a8a; color: white; padding: 15px 20px; font-size: 1.1rem; font-weight: 700; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .pin-badge { background-color: #f59e0b; color: #000; padding: 6px 14px; border-radius: 20px; font-size: 1.2rem; font-weight: 800; letter-spacing: 1px; }
        .container { max-width: 900px; margin: 20px auto; padding: 10px; }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 25px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; box-sizing: border-box; }
        .hint-text { font-size: 0.85rem; color: #2563eb; margin-top: 4px; font-weight: 500; }
        button { background-color: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 1rem; font-weight: 500; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #1d4ed8; }
        .btn-correct { background-color: #10b981; font-size: 1.3rem; padding: 15px 35px; }
        .btn-wrong { background-color: #ef4444; font-size: 1.3rem; padding: 15px 35px; }
        .btn-stop { background-color: #f59e0b; }
        .score-box { display: inline-block; width: 30px; height: 30px; line-height: 30px; text-align: center; border-radius: 50%; margin-right: 5px; color: white; font-weight: 700; }
        .score-1 { background-color: #10b981; }
        .score-0 { background-color: #ef4444; }
        .grid-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }
        .report-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .report-table th, .report-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .report-table th { background-color: #e2e8f0; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 700; color: white; }
        .badge-info { background-color: #3b82f6; }
        .badge-warning { background-color: #f59e0b; }
        .badge-danger { background-color: #ef4444; }
        .bar-chart { background-color: #e2e8f0; border-radius: 4px; height: 24px; width: 100%; margin-top: 5px; overflow: hidden; }
        .bar-fill { background-color: #3b82f6; height: 100%; }
        .pin-box { background: #eff6ff; border: 2px dashed #3b82f6; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <div>🔍 국립특수교육원 기초학습능력 25분 통합 스크리닝 (Reading, Writing, Math)</div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span>🔑 내 방 번호(PIN):</span>
            <span id="pin-display" class="pin-badge">생성 중...</span>
            <button onclick="createNewRoom()" style="padding:6px 12px; font-size:0.85rem; background:#475569;">🔄 새 방 만들기</button>
        </div>
    </div>
    <div class="container">
        
        <!-- 1. 아동 등록 카드 -->
        <div id="card-setup" class="card">
            <div class="pin-box">
                <h3 style="margin:0 0 5px 0; color:#1e3a8a;">📱 아동용 태블릿 접속 방법</h3>
                <p style="margin:0; font-size:1.1rem; color:#1e293b;">
                    태블릿 브라우저에서 아래 주소로 접속한 후, 방 번호 <strong id="student-pin-hint" style="color:#d97706; font-size:1.4rem;">----</strong>를 입력하세요.<br>
                    <small style="color:#64748b;">(직접 접속 주소: <a id="direct-student-link" href="#" target="_blank" style="color:#2563eb; font-weight:700;">/student?room=...</a>)</small>
                </p>
            </div>

            <h2 style="margin-top:0;">📝 평가 아동 정보 등록</h2>
            <div class="form-group">
                <label>아동 이름</label>
                <input type="text" id="input-name" placeholder="예: 김민수" value="김민수">
            </div>
            <div class="form-group">
                <label>아동 연령/학년 (만 나이)</label>
                <select id="select-grade" onchange="autoSelectPreset()">
                    <option value="유치원 / 영유아 (만 3세)">유치원 / 영유아 (만 3세)</option>
                    <option value="유치원 / 영유아 (만 4세)">유치원 / 영유아 (만 4세)</option>
                    <option value="유치원 / 영유아 (만 5세)">유치원 / 영유아 (만 5세)</option>
                    <option value="초등학교 1학년 (만 6세)" selected>초등학교 1학년 (만 6세)</option>
                    <option value="초등학교 2학년 (만 7세)">초등학교 2학년 (만 7세)</option>
                    <option value="초등학교 3학년 (만 8세)">초등학교 3학년 (만 8세)</option>
                    <option value="초등학교 4학년 (만 9세)">초등학교 4학년 (만 9세)</option>
                    <option value="초등학교 5학년 (만 10세)">초등학교 5학년 (만 10세)</option>
                    <option value="초등학교 6학년 (만 11세)">초등학교 6학년 (만 11세)</option>
                    <option value="중학교 1학년 (만 12세)">중학교 1학년 (만 12세)</option>
                    <option value="중학교 2학년 (만 13세)">중학교 2학년 (만 13세)</option>
                    <option value="중학교 3학년 (만 14세)">중학교 3학년 (만 14세)</option>
                    <option value="고등학교 1학년 (만 15세)">고등학교 1학년 (만 15세)</option>
                    <option value="고등학교 2학년 (만 16세)">고등학교 2학년 (만 16세)</option>
                    <option value="고등학교 3학년 (만 17세)">고등학교 3학년 (만 17세)</option>
                </select>
                <div class="hint-text" id="age-hint">💡 선택하신 연령에 맞는 스크리닝 모듈이 자동 지정되었습니다.</div>
            </div>
            <div class="form-group">
                <label>통합 스크리닝 진단 모듈 선택 (선생님 수동 변경 가능)</label>
                <select id="select-preset">
                    <option value="1" selected>1. 초1 스크리닝 (기초 해독 & 수 개념)</option>
                    <option value="2">2. 초3 발달지체 재심의 (결손 보완 분기)</option>
                    <option value="3">3. 중입 (교과 문해력 & 수학)</option>
                    <option value="4">4. 고입 (~중3 전환기 기능적 평가)</option>
                </select>
            </div>
            <button onclick="startSession()" style="width:100%; font-size:1.2rem; padding:15px;">🚀 통합 스크리닝 연동 및 검사 시작</button>
        </div>

        <!-- 2. 실시간 검사 통제 카드 -->
        <div id="card-exam" class="card" style="display:none;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 id="exam-domain" style="margin:0; color:#1e3a8a;"></h3>
                <span class="badge badge-info" id="exam-preset-name"></span>
            </div>
            <h1 id="exam-subtest" style="margin-top:10px; margin-bottom:5px; font-size:1.8rem;"></h1>
            
            <div id="consecutive-warning-box" class="badge badge-danger" style="display:none; margin-bottom:15px; font-size:0.95rem; padding:8px 12px; width:100%; box-sizing:border-box; text-align:center;">
                ⚠️ 경고: 연속 2회 오답! 1번 더 틀리면 자동 중지 규칙이 작동합니다.
            </div>

            <!-- 현재 문제 제시 카드 -->
            <div style="background-color:#f8fafc; border-left:6px solid #2563eb; padding:20px; border-radius:4px; margin:15px 0;">
                <div style="font-size:0.9rem; color:#64748b;">아동 화면 송출 중:</div>
                <div id="exam-question" style="font-size:2.5rem; font-weight:700; margin:10px 0; color:#0f172a;"></div>
                <hr style="border:0; border-top:1px solid #e2e8f0; margin:15px 0;">
                <div id="exam-guide" style="font-size:1.1rem; color:#475569; font-weight:500; line-height:1.5;"></div>
                <div id="exam-answer" style="font-size:1.1rem; color:#10b981; font-weight:700; margin-top:5px;"></div>
            </div>

            <!-- 현재 하위검사 실시간 득점 현황 -->
            <div id="subtest-score-flow" style="margin:15px 0;">
                <span style="font-weight:500; color:#64748b; margin-right:10px;">현재 영역 채점 현황:</span>
                <span id="score-flow-container"></span>
            </div>

            <!-- 채점 및 통제 버튼 -->
            <div class="grid-buttons" id="exam-actions">
                <button class="btn-correct" onclick="gradeItem(1)">🟢 맞음 (1점)</button>
                <button class="btn-wrong" onclick="gradeItem(0)">❌ 틀림 (0점)</button>
            </div>
            
            <div style="margin-top:20px; text-align:right;">
                <button class="btn-stop" onclick="skipToNextSubtest()">하위검사 건너뛰기 ➡️</button>
            </div>
        </div>

        <!-- 3. 검사 중지 안내 카드 -->
        <div id="card-stop" class="card" style="display:none; border-top:8px solid #ef4444; text-align:center;">
            <h1 style="color:#ef4444; margin-top:0;">🛑 자동 중지 규칙(Stop Rule) 작동</h1>
            <p style="font-size:1.2rem; line-height:1.6;">
                아동이 <strong style="color:#ef4444;">연속 3개 문항을 틀려</strong> 더 이상의 평가 진행은 좌절감을 높일 우려가 있어<br>
                해당 하위검사를 중지하고 다음 검사로 전환합니다.
            </p>
            <p style="color:#64748b;">(아동 화면은 편안한 대기 화면으로 자동 복구되었습니다.)</p>
            <button onclick="resumeNextSubtest()" style="background-color:#10b981; font-size:1.2rem; padding:15px 30px;">다음 하위검사로 계속 진행하기 ➡️</button>
        </div>

        <!-- 4. 결과 및 IEP 보고서 카드 -->
        <div id="card-report" class="card" style="display:none; border-top:8px solid #10b981;">
            <h1 style="color:#10b981; margin-top:0; text-align:center;">📊 기초학습능력 통합 스크리닝 결과 & IEP 권고 리포트</h1>
            <div style="background-color:#f1f5f9; padding:15px; border-radius:8px; margin-bottom:20px;">
                <h3 style="margin-top:0; color:#334155;">피평가자 인적사항</h3>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">
                    <div>👤 <strong>이름:</strong> <span id="rep-name"></span></div>
                    <div>🎒 <strong>연령/학년:</strong> <span id="rep-grade"></span></div>
                    <div>📑 <strong>진단모듈:</strong> <span id="rep-preset"></span></div>
                </div>
            </div>

            <!-- 영역별 점수 통계 표 및 그래프 -->
            <h3>📈 소검사별 수행도 프로파일</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>소검사 영역</th>
                        <th>원점수 / 총문항</th>
                        <th>정답률 (%)</th>
                        <th>발달 수준 판정</th>
                    </tr>
                </thead>
                <tbody id="report-table-body">
                </tbody>
            </table>

            <!-- 보완검사 자동 분기 결과 안내 -->
            <div id="supplementary-section" class="card" style="display:none; background-color:#fffbeb; border:1px solid #fef3c7; margin-top:20px;">
                <h3 style="margin-top:0; color:#d97706;">⚠️ 80% 미만 결손 발견: 정밀 보완검사 추천</h3>
                <p id="supplementary-message" style="line-height:1.5;"></p>
                <button onclick="startSupplementaryTest()" style="background-color:#d97706;">보완 검사 연동 실시하기</button>
            </div>

            <!-- 개별화 교육 중재(IEP) 전략 제안 -->
            <h3>💡 특수교육 중재 계획(IEP) 가이드라인</h3>
            <div id="iep-guideline-box" style="background-color:#eff6ff; border-left:6px solid #3b82f6; padding:15px; border-radius:4px; line-height:1.6;">
            </div>
            
            <div style="margin-top:25px; text-align:center;">
                <button onclick="resetTest()" style="background-color:#64748b;">🔄 새 아동 검사 실시하기</button>
            </div>
        </div>

    </div>

    <script>
        var currentRoomId = sessionStorage.getItem("teacher_room_id") || "";

        function autoSelectPreset() {
            var gradeVal = document.getElementById("select-grade").value;
            var presetSelect = document.getElementById("select-preset");
            var hintElem = document.getElementById("age-hint");

            if (gradeVal.includes("만 3세") || gradeVal.includes("만 4세") || gradeVal.includes("만 5세") || gradeVal.includes("만 6세")) {
                presetSelect.value = "1";
                hintElem.innerText = "💡 만 3~6세 연령에 맞춰 '1. 초1 스크리닝 모드'가 자동 추천되었습니다.";
            } else if (gradeVal.includes("만 7세") || gradeVal.includes("만 8세") || gradeVal.includes("만 9세") || gradeVal.includes("만 10세")) {
                presetSelect.value = "2";
                hintElem.innerText = "💡 만 7~10세 연령에 맞춰 '2. 초3 발달지체 재심의 모드'가 자동 추천되었습니다.";
            } else if (gradeVal.includes("만 11세") || gradeVal.includes("만 12세") || gradeVal.includes("만 13세") || gradeVal.includes("만 14세")) {
                presetSelect.value = "3";
                hintElem.innerText = "💡 만 11~14세 연령에 맞춰 '3. 중입 교과 문해력 & 수학 모드'가 자동 추천되었습니다.";
            } else {
                presetSelect.value = "4";
                hintElem.innerText = "💡 만 15~17세 연령에 맞춰 '4. 고입 전환기 기능적 평가 모드'가 자동 추천되었습니다.";
            }
        }

        function initRoom() {
            if (!currentRoomId) {
                createNewRoom();
            } else {
                updatePinDisplay(currentRoomId);
                pollState();
            }
            autoSelectPreset();
        }

        function createNewRoom() {
            fetch('/api/create_room', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    currentRoomId = data.room_id;
                    sessionStorage.setItem("teacher_room_id", currentRoomId);
                    updatePinDisplay(currentRoomId);
                    pollState();
                });
        }

        function updatePinDisplay(pin) {
            document.getElementById("pin-display").innerText = pin;
            document.getElementById("student-pin-hint").innerText = pin;
            var directUrl = window.location.origin + "/student?room=" + pin;
            var linkElem = document.getElementById("direct-student-link");
            linkElem.innerText = "/student?room=" + pin;
            linkElem.href = directUrl;
        }

        function pollState() {
            if (!currentRoomId) return;
            fetch('/api/state?room=' + currentRoomId)
                .then(res => {
                    if (!res.ok) {
                        createNewRoom();
                        throw new Error('Room expired');
                    }
                    return res.json();
                })
                .then(state => {
                    renderState(state);
                })
                .catch(err => console.log(err));
        }

        setInterval(pollState, 1000);

        function startSession() {
            var name = document.getElementById("input-name").value;
            var grade = document.getElementById("select-grade").value;
            var preset = document.getElementById("select-preset").value;
            
            fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    "room_id": currentRoomId,
                    "student_name": name,
                    "student_grade": grade,
                    "preset_mode": preset
                })
            }).then(() => pollState());
        }

        function gradeItem(isCorrect) {
            fetch('/api/grade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "room_id": currentRoomId, "score": isCorrect })
            }).then(() => pollState());
        }

        function skipToNextSubtest() {
            fetch('/api/skip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "room_id": currentRoomId })
            }).then(() => pollState());
        }

        function resumeNextSubtest() {
            fetch('/api/resume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "room_id": currentRoomId })
            }).then(() => pollState());
        }

        function startSupplementaryTest() {
            fetch('/api/supplementary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "room_id": currentRoomId })
            }).then(() => pollState());
        }

        function resetTest() {
            fetch('/api/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "room_id": currentRoomId })
            }).then(() => pollState());
        }

        function renderState(state) {
            if (!state.student_name) {
                document.getElementById("card-setup").style.display = "block";
                document.getElementById("card-exam").style.display = "none";
                document.getElementById("card-stop").style.display = "none";
                document.getElementById("card-report").style.display = "none";
                return;
            }

            document.getElementById("card-setup").style.display = "none";

            if (state.stop_triggered) {
                document.getElementById("card-exam").style.display = "none";
                document.getElementById("card-stop").style.display = "block";
                document.getElementById("card-report").style.display = "none";
                return;
            } else {
                document.getElementById("card-stop").style.display = "none";
            }

            if (state.test_completed) {
                document.getElementById("card-exam").style.display = "none";
                document.getElementById("card-report").style.display = "block";
                
                document.getElementById("rep-name").innerText = state.student_name;
                document.getElementById("rep-grade").innerText = state.student_grade;
                document.getElementById("rep-preset").innerText = state.preset_name;

                buildReport(state);
                return;
            } else {
                document.getElementById("card-report").style.display = "none";
            }

            document.getElementById("card-exam").style.display = "block";
            document.getElementById("exam-domain").innerText = state.domain_title;
            document.getElementById("exam-preset-name").innerText = state.preset_name + (state.supplementary_active ? " (보완 검사)" : "");
            document.getElementById("exam-subtest").innerText = state.subtest_title;
            document.getElementById("exam-question").innerText = state.current_question;
            document.getElementById("exam-guide").innerText = "💡 지시문: " + state.current_guide;
            document.getElementById("exam-answer").innerText = "🔑 예시 정답: " + state.current_answer;

            var scoreFlowContainer = document.getElementById("score-flow-container");
            scoreFlowContainer.innerHTML = "";
            
            var current_sub_key = "";
            for (var key in TEST_CONTENT) {
                for (var s_key in TEST_CONTENT[key]["subtests"]) {
                    if (TEST_CONTENT[key]["subtests"][s_key]["name"] === state.subtest_title) {
                        current_sub_key = key + "_" + s_key;
                    }
                }
            }

            var consecutiveWrongCount = 0;
            if (current_sub_key && state.scores[current_sub_key]) {
                var scoresList = state.scores[current_sub_key];
                scoresList.forEach(function(sc) {
                    var span = document.createElement("span");
                    span.className = "score-box score-" + sc;
                    span.innerText = sc === 1 ? "O" : "X";
                    scoreFlowContainer.appendChild(span);

                    if (sc === 0) {
                        consecutiveWrongCount++;
                    } else {
                        consecutiveWrongCount = 0;
                    }
                });
            }

            if (consecutiveWrongCount >= 2) {
                document.getElementById("consecutive-warning-box").style.display = "block";
            } else {
                document.getElementById("consecutive-warning-box").style.display = "none";
            }
        }

        function buildReport(state) {
            var tbody = document.getElementById("report-table-body");
            tbody.innerHTML = "";

            var totalPossible = 0;
            var totalCorrect = 0;
            var lowScoreDetected = false;

            for (var subKey in state.scores) {
                var scoresList = state.scores[subKey];
                var subCorrect = scoresList.reduce((a, b) => a + b, 0);
                var subTotal = scoresList.length;

                var maxQuestions = 5;
                var displayName = subKey;
                for (var dom in TEST_CONTENT) {
                    for (var sub in TEST_CONTENT[dom]["subtests"]) {
                        if (dom + "_" + sub === subKey) {
                            maxQuestions = TEST_CONTENT[dom]["subtests"][sub]["questions"].length;
                            displayName = TEST_CONTENT[dom]["subtests"][sub]["name"];
                        }
                    }
                }

                var pct = subTotal > 0 ? Math.round((subCorrect / subTotal) * 100) : 0;
                
                var level = "정상 범주";
                var levelClass = "badge-info";
                if (pct < 50) {
                    level = "장애 위험군 (High Risk)";
                    levelClass = "badge-danger";
                    lowScoreDetected = true;
                } else if (pct < 80) {
                    level = "경계선 / 학습지체";
                    levelClass = "badge-warning";
                    lowScoreDetected = true;
                }

                var tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${displayName}</strong></td>
                    <td>${subCorrect} / ${subTotal} (완료율: ${Math.round(subTotal/maxQuestions*100)}%)</td>
                    <td>
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span>${pct}%</span>
                            <div class="bar-chart" style="width: 80px;">
                                <div class="bar-fill" style="width: ${pct}%; background-color: ${pct < 50 ? '#ef4444' : (pct < 80 ? '#f59e0b' : '#10b981')};"></div>
                            </div>
                        </div>
                    </td>
                    <td><span class="badge ${levelClass}">${level}</span></td>
                `;
                tbody.appendChild(tr);

                totalCorrect += subCorrect;
                totalPossible += subTotal;
            }

            var suppSection = document.getElementById("supplementary-section");
            if (state.supplementary_recommended.length > 0 && !state.supplementary_active) {
                suppSection.style.display = "block";
                document.getElementById("supplementary-message").innerHTML = `
                    학생의 통합 스크리닝 결과 학습 결손(80% 미만) 영역이 확인되었습니다.<br>
                    <strong>특수교육 요강 지능형 분기 지침</strong>에 맞춰 추천되는 정밀 보완검사:<br>
                    🎁 <strong>추천 보완 검사:</strong> <span style='color:#d97706; font-weight:700;'>${state.supplementary_recommended.join(", ")}</span>
                `;
            } else {
                suppSection.style.display = "none";
            }

            var iepBox = document.getElementById("iep-guideline-box");
            if (lowScoreDetected) {
                iepBox.innerHTML = `
                    <p style="margin-top:0;"><strong>📌 종합 스크리닝 진단: 특수교육적 중재 및 맞춤형 지원 필요</strong></p>
                    <ul>
                        <li><strong>국어(읽기/쓰기):</strong> 기초 음운 처리 및 글씨 가독성/철자하기에서 결손이 발견되었습니다. 다감각(Multisensory) 읽기-쓰기 연계 훈련을 매일 15분씩 지원해 주세요.</li>
                        <li><strong>수학(수/연산/도형):</strong> 연산 자동화 및 수 개념 보완이 필요합니다. 실물 교구(수 모형) 및 구체물을 활용한 시각적 연산 중재를 추천합니다.</li>
                    </ul>
                `;
            } else {
                iepBox.innerHTML = `
                    <p style="margin-top:0;"><strong>📌 종합 스크리닝 진단: 정상 범주 발달</strong></p>
                    <ul>
                        <li>현재 선택된 통합 스크리닝 영역에서 아동의 발달 상태는 정상 범주에 도달해 있습니다.</li>
                        <li>향후 교과 문해력 및 수학적 사고력 신장을 위해 응용 문제 풀이 위주의 지도를 권장합니다.</li>
                    </ul>
                `;
            }
        }

        initRoom();
    </script>
</body>
</html>
"""

# 아동용 UI HTML
STUDENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>아동용 제시 화면 (Student Screen)</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #ffffff;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
            user-select: none;
            -webkit-user-select: none;
        }
        .canvas-container {
            text-align: center;
            width: 90%;
            max-width: 1000px;
        }
        .giant-text {
            font-size: 6.5rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.3;
            word-break: keep-all;
            transition: all 0.2s ease-in-out;
        }
        .story-text {
            font-size: 2.2rem;
            line-height: 1.6;
            text-align: left;
            background-color: #f8fafc;
            padding: 30px;
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            max-height: 70vh;
            overflow-y: auto;
        }
        .waiting-screen {
            color: #64748b;
        }
        .waiting-text {
            font-size: 2.5rem;
            margin-top: 20px;
        }
        .pulse {
            animation: pulse-animation 2s infinite;
        }
        @keyframes pulse-animation {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .pin-input-box {
            background-color: #f1f5f9;
            padding: 40px;
            border-radius: 16px;
            border: 2px dashed #94a3b8;
            max-width: 450px;
            margin: 0 auto;
        }
        .pin-input-field {
            font-size: 3rem;
            font-weight: 800;
            letter-spacing: 10px;
            text-align: center;
            width: 220px;
            padding: 10px;
            border: 3px solid #3b82f6;
            border-radius: 12px;
            margin: 20px 0;
            outline: none;
        }
        .pin-submit-btn {
            background-color: #2563eb;
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="canvas-container">
        
        <!-- 0. PIN 번호 입력 화면 -->
        <div id="student-pin-screen" class="pin-input-box">
            <div style="font-size: 4rem;">🔑</div>
            <h2 style="font-size: 2rem; color: #1e293b; margin: 10px 0;">선생님 방 번호(PIN) 입력</h2>
            <p style="color: #64748b; font-size: 1.2rem; margin: 0;">교사 화면에 표시된 4자리 숫자를 입력하세요.</p>
            <input type="text" id="pin-input" class="pin-input-field" maxlength="4" placeholder="1234">
            <br>
            <button class="pin-submit-btn" onclick="submitPin()">검사방 입장하기 ➡️</button>
            <p id="pin-error-msg" style="color: #ef4444; font-size: 1.1rem; margin-top: 15px; display: none;"></p>
        </div>

        <!-- 1. 대기 화면 -->
        <div id="student-waiting" class="waiting-screen" style="display:none;">
            <div class="giant-emoji pulse">📖</div>
            <div class="waiting-text" id="waiting-message">반갑습니다!<br>선생님과 함께 재미있는 공부를 시작해봐요.</div>
        </div>

        <!-- 2. 문제 자극 화면 -->
        <div id="student-exam" style="display:none;">
            <div id="question-area" class="giant-text"></div>
        </div>

    </div>

    <script>
        var studentRoomId = "";

        function checkUrlRoom() {
            var urlParams = new URLSearchParams(window.location.search);
            var roomParam = urlParams.get('room');
            if (roomParam && roomParam.length === 4) {
                studentRoomId = roomParam;
                document.getElementById("pin-input").value = roomParam;
                connectToRoom(studentRoomId);
            }
        }

        function submitPin() {
            var inputVal = document.getElementById("pin-input").value.trim();
            if (inputVal.length !== 4) {
                showError("4자리 숫자 PIN 번호를 정확히 입력해주세요.");
                return;
            }
            connectToRoom(inputVal);
        }

        function showError(msg) {
            var errElem = document.getElementById("pin-error-msg");
            errElem.innerText = msg;
            errElem.style.display = "block";
        }

        function connectToRoom(roomId) {
            fetch('/api/state?room=' + roomId)
                .then(res => {
                    if (!res.ok) {
                        throw new Error("존재하지 않는 방 번호입니다.");
                    }
                    return res.json();
                })
                .then(state => {
                    studentRoomId = roomId;
                    document.getElementById("student-pin-screen").style.display = "none";
                    document.getElementById("pin-error-msg").style.display = "none";
                    renderStudentState(state);
                    startPolling();
                })
                .catch(err => {
                    showError("⚠️ " + err.message);
                });
        }

        function startPolling() {
            setInterval(function() {
                if (!studentRoomId) return;
                fetch('/api/state?room=' + studentRoomId)
                    .then(res => res.json())
                    .then(state => renderStudentState(state))
                    .catch(err => console.log(err));
            }, 1000);
        }

        function renderStudentState(state) {
            var waitingDiv = document.getElementById("student-waiting");
            var examDiv = document.getElementById("student-exam");
            var qArea = document.getElementById("question-area");
            var waitingMsg = document.getElementById("waiting-message");

            if (!state.student_name) {
                waitingDiv.style.display = "block";
                examDiv.style.display = "none";
                waitingMsg.innerHTML = "반갑습니다! 👋<br>선생님과 함께 재미있는 공부를 시작해봐요.";
                return;
            }

            if (state.stop_triggered) {
                waitingDiv.style.display = "block";
                examDiv.style.display = "none";
                waitingMsg.innerHTML = "🎨 정말 잘했어요!<br>잠시만 기다리시면 선생님께서 다음 활동을 안내해 주실 거예요.";
                return;
            }

            if (state.test_completed) {
                waitingDiv.style.display = "block";
                examDiv.style.display = "none";
                waitingMsg.innerHTML = "🌟 검사가 모두 끝났습니다! 🌟<br>열심히 공부해줘서 정말 고마워요!";
                return;
            }

            waitingDiv.style.display = "none";
            examDiv.style.display = "block";

            var questionText = state.current_question;
            
            if (state.is_ran_or_flow) {
                if (questionText.length > 30) {
                    qArea.className = "story-text";
                } else {
                    qArea.className = "giant-text";
                    qArea.style.fontSize = "5.5rem";
                }
            } else {
                qArea.className = "giant-text";
                qArea.style.fontSize = "7.5rem";
            }

            qArea.innerText = questionText;
        }

        checkUrlRoom();
    </script>
</body>
</html>
"""

@app.get("/teacher", response_class=HTMLResponse)
async def get_teacher():
    return HTMLResponse(content=TEACHER_HTML)

@app.get("/student", response_class=HTMLResponse)
async def get_student():
    return HTMLResponse(content=STUDENT_HTML)

@app.get("/", response_class=HTMLResponse)
async def redirect_root():
    return HTMLResponse(content="""
    <div style="font-family: sans-serif; text-align: center; margin-top: 60px; padding: 20px;">
        <h2>🎒 국립특수교육원 기초학습능력 통합 스크리닝 시스템 (Reading, Writing, Math)</h2>
        <p style="color: #475569; font-size: 1.1rem;">국어 및 수학 3대 영역을 25분 안에 신속하게 평가하는 스마트 연동 시스템입니다.</p>
        
        <div style="margin: 30px auto; max-width: 600px; text-align: left; background: #f8fafc; padding: 30px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; color:#1e3a8a;">📱 접속 안내:</h3>
            <div style="margin-bottom: 20px;">
                <p><strong>1. 교사 채점용 패널:</strong></p>
                <a href="/teacher" style="display:inline-block; background:#2563eb; color:white; padding:12px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">📱 교사용 화면 바로가기 (PIN 생성)</a>
            </div>
            <hr style="border:0; border-top:1px solid #cbd5e1; margin:20px 0;">
            <div>
                <p><strong>2. 아동 제시용 태블릿:</strong></p>
                <a href="/student" style="display:inline-block; background:#10b981; color:white; padding:12px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">💻 아동용 화면 바로가기 (PIN 입력)</a>
            </div>
        </div>
    </div>
    """)

if __name__ == "__main__":
    port = 8000
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
