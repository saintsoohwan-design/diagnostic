# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import socket
import random
import time

app = FastAPI(title="국립특수교육원 기초학습기능검사 다중방 스마트 연동 시스템 (Multi-Room HTTP Polling)")

# 검사 데이터 정의
TEST_CONTENT = {
    "phoneme": {
        "title": "I. 음운 처리",
        "subtests": {
            "blending": {
                "name": "1. 음절 합성",
                "stop_rule": 3,
                "questions": [
                    {"q": "/편/ + /지/", "a": "편지", "guide": "선생님: '/편/ 소리와 /지/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/토/ + /끼/", "a": "토끼", "guide": "선생님: '/토/ 소리와 /끼/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/감/ + /사/", "a": "감사", "guide": "선생님: '/감/ 소리와 /사/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/마/ + /음/", "a": "마음", "guide": "선생님: '/마/ 소리와 /음/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/애/ + /벌/ + /레/", "a": "애벌레", "guide": "선생님: '/애/ 소리와 /벌/ 소리와 /레/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/비/ + /둘/ + /기/", "a": "비둘기", "guide": "선생님: '/비/ 소리와 /둘/ 소리와 /기/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/방/ + /송/ + /국/", "a": "방송국", "guide": "선생님: '/방/ 소리와 /송/ 소리와 /국/ 소리를 합하면 무슨 소리가 될까요?'"},
                    {"q": "/이/ + /야/ + /기/", "a": "이야기", "guide": "선생님: '/이/ 소리와 /야/ 소리와 /기/ 소리를 합하면 무슨 소리가 될까요?'"}
                ]
            },
            "ran_object": {
                "name": "6-1. 빠른 이름대기 (사물)",
                "stop_rule": 99,
                "type": "ran",
                "questions": [
                    {
                        "q": "⚽️ 🍚 🐎 🥛 ✋", 
                        "a": "축구공, 밥, 말, 컵, 손", 
                        "guide": "1분간 아동이 왼쪽에서 오른쪽으로 빠르게 그림 이름을 대도록 하세요. 교사는 오독/빠뜨린 항목만 실시간 체크합니다."
                    }
                ]
            },
            "ran_color": {
                "name": "6-2. 빠른 이름대기 (색깔)",
                "stop_rule": 99,
                "type": "ran",
                "questions": [
                    {
                        "q": "🟥 🟨 🟩 🟦 ⬛", 
                        "a": "빨강, 노랑, 초록, 파랑, 검정", 
                        "guide": "1분간 아동이 빠르게 색깔 이름을 대도록 하세요."
                    }
                ]
            }
        }
    },
    "word": {
        "title": "II. 글자·단어 인지",
        "subtests": {
            "letter": {
                "name": "1. 낱글자 인지",
                "stop_rule": 3,
                "questions": [
                    {"q": "ㄹ", "a": "리을", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㅂ", "a": "비읍", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㅈ", "a": "지읒", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㅊ", "a": "치읓", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㅎ", "a": "히읗", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㅆ", "a": "쌍시옷", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㄲ", "a": "쌍기역", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"},
                    {"q": "ㅌ", "a": "티읕", "guide": "이 낱글자의 이름은 무엇일까요? (3초 반응)"}
                ]
            },
            "regular_word": {
                "name": "2-1. 단어 인지 (규칙단어)",
                "stop_rule": 3,
                "questions": [
                    {"q": "감", "a": "감", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "선물", "a": "선물", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "상", "a": "상", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "병원", "a": "병원", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "이루다", "a": "이루다", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "냄새", "a": "냄새", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "잔치", "a": "잔치", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "오랜만", "a": "오랜만", "guide": "이 단어를 소리 내어 읽어보세요."}
                ]
            },
            "irregular_word": {
                "name": "2-2. 단어 인지 (불규칙단어)",
                "stop_rule": 3,
                "questions": [
                    {"q": "꽃", "a": "꼳", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "부엌", "a": "부억", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "국민", "a": "궁민", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "비눗물", "a": "비눈물", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "축하", "a": "추카", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "덥다", "a": "덥따", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "낱말", "a": "난말", "guide": "이 단어를 소리 내어 읽어보세요."},
                    {"q": "많다", "a": "만타", "guide": "이 단어를 소리 내어 읽어보세요."}
                ]
            }
        }
    },
    "fluency": {
        "title": "III. 유창성",
        "subtests": {
            "dog_story": {
                "name": "1. 글 읽기 유창성 (개 이야기)",
                "stop_rule": 99,
                "type": "text_flow",
                "questions": [
                    {
                        "q": "개는 사람이 집에서 기르는 동물 중에서 가장 오래된 동물입니다. 그래서 세계 어느 나라에서나 개를 기르는 모습을 볼 수 있습니다. 우리나라에서 옛날부터 기르던 개로는 진돗개, 삽살개, 풍산개가 있습니다. 이들은 각각 다른 특수성을 가지고 있습니다. 옛날 진도에서는 사냥꾼이 총 한 방 쏘지 않고 동물을 잡았습니다. 그 이유는 사냥할 때 진돗개를 데리고 가면 진돗개가 사슴이나 토끼를 다 잡아왔기 때문입니다...", 
                        "a": "분당 정확히 읽은 음절 수 채점", 
                        "guide": "아동이 1분 동안 글을 소리 내어 읽도록 하세요. 교사는 실시간으로 오독 음절 수를 카운트합니다."
                    }
                ]
            }
        }
    },
    "vocab": {
        "title": "IV. 어휘",
        "subtests": {
            "matching_pic": {
                "name": "1. 단어가 뜻하는 그림 찾기",
                "stop_rule": 3,
                "questions": [
                    {"q": "놀이터 🛝", "a": "1번 그림", "guide": "제시된 어휘 '놀이터'에 알맞은 그림(보기 1번)을 고르게 하세요."},
                    {"q": "소방관 🧑‍🚒", "a": "4번 그림", "guide": "어휘 '소방관'에 알맞은 소방관 그림(보기 4번)을 아동이 터치하게 하세요."}
                ]
            },
            "antonym": {
                "name": "2. 반대말 대기",
                "stop_rule": 3,
                "questions": [
                    {"q": "더하다", "a": "빼다", "guide": "'더하다'의 반대말은 무엇일까요? (5초 무응답 시 오답)"},
                    {"q": "위", "a": "아래 / 밑", "guide": "'위'의 반대말은 무엇일까요?"},
                    {"q": "쉽다", "a": "어렵다 / 난해하다", "guide": "'쉽다'의 반대말은 무엇일까요?"},
                    {"q": "조용하다", "a": "시끄럽다 / 소란스럽다", "guide": "'조용하다'의 반대말은 무엇일까요?"}
                ]
            },
            "analogy": {
                "name": "3. 어휘 유추",
                "stop_rule": 3,
                "questions": [
                    {"q": "손 : 장갑 = 발 : ( ? )", "a": "양말 / 신발", "guide": "손에 장갑을 끼듯이 발에는 무엇을 신을까요?"},
                    {"q": "낮 : 태양 = 밤 : ( ? )", "a": "달 / 별", "guide": "낮에는 태양이 뜨고 밤에는 무엇이 떠오를까요?"}
                ]
            },
            "blank_fill": {
                "name": "4. 빈칸 채우기",
                "stop_rule": 3,
                "questions": [
                    {"q": "비가 오면 ( ? )을 씁니다.", "a": "우산", "guide": "문맥에 맞는 단어를 말해보세요."},
                    {"q": "배가 고파서 ( ? )을 먹었습니다.", "a": "밥 / 음식 / 빵", "guide": "문맥에 맞는 단어를 말해보세요."}
                ]
            }
        }
    },
    "comprehension": {
        "title": "V. 읽기 이해",
        "subtests": {
            "sentence_under": {
                "name": "1. 문장 이해",
                "stop_rule": 3,
                "questions": [
                    {"q": "손을 머리 위로 드세요.", "a": "동작 수행", "guide": "아동에게 문장을 조용히 읽고, 그 내용을 몸으로 표현하도록 하세요."},
                    {"q": "뒤로 돌아서 손뼉을 세 번 치세요.", "a": "동작 수행", "guide": "문장을 조용히 읽고 내용을 몸으로 표현하게 하세요."}
                ]
            }
        }
    }
}

# 4대 대상군별 프리셋 매핑
PRESET_MAPPING = {
    "1": {
        "name": "초1 (기초 해독 & 문해력 스크리닝)",
        "desc": "초1 기초 음운, 글자·단어 인지, 글씨쓰기 및 기초 철자 진단 모드",
        "domains": [("phoneme", "blending"), ("word", "letter"), ("word", "regular_word"), ("vocab", "matching_pic"), ("comprehension", "sentence_under")]
    },
    "2": {
        "name": "초3 발달지체 재심의 (결손 보완 분기 모드)",
        "desc": "초3 재심의용 유창성, 어휘, 독해, 쓰기 평가 및 80% 미만 시 음운/해독 하향 보완 분기",
        "domains": [("fluency", "dog_story"), ("vocab", "antonym"), ("vocab", "blank_fill"), ("comprehension", "sentence_under")]
    },
    "3": {
        "name": "중입 (초6~중1 교과 문해력 진단)",
        "desc": "중학교 입학 대비 어휘, 긴 글 독해, 문법 지식, 쓰기 유창성 평가 모드",
        "domains": [("vocab", "antonym"), ("vocab", "analogy"), ("vocab", "blank_fill"), ("comprehension", "sentence_under")]
    },
    "4": {
        "name": "고입 (~중3 전환기 기능적 평가 모드)",
        "desc": "고등학교 진학 대비 기능적 어휘, 고난도 추론 독해, 논리적 문장 구성력 평가 모드",
        "domains": [("vocab", "analogy"), ("vocab", "blank_fill"), ("comprehension", "sentence_under")]
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
        if self.student_grade == "초등학교 2학년":
            for sub_key, scores in self.scores.items():
                correct_pct = sum(scores) / len(scores) if len(scores) > 0 else 1.0
                if correct_pct < 0.8:
                    self.supplementary_recommended.append("음운 처리 보완검사")
                    break
        elif "초등학교 3학년" in self.student_grade or "초등학교 4학년" in self.student_grade:
            for sub_key, scores in self.scores.items():
                correct_pct = sum(scores) / len(scores) if len(scores) > 0 else 1.0
                if correct_pct < 0.8:
                    self.supplementary_recommended.append("음운 처리 보완검사")
                    self.supplementary_recommended.append("글자·단어 인지 보완검사")
                    break

# 글로벌 다중 검사방 저장소
ROOMS: Dict[str, RoomState] = {}

def get_or_create_room(room_id: Optional[str] = None) -> RoomState:
    if room_id and room_id in ROOMS:
        return ROOMS[room_id]
    
    # 4자리 랜덤 PIN 생성 (기존 PIN 중복 방지)
    for _ in range(100):
        new_pin = str(random.randint(1000, 9999))
        if new_pin not in ROOMS:
            ROOMS[new_pin] = RoomState(new_pin)
            return ROOMS[new_pin]
            
    # fallback
    fallback_pin = str(time.time_ns())[-4:]
    ROOMS[fallback_pin] = RoomState(fallback_pin)
    return ROOMS[fallback_pin]

# REST API Models & Endpoints
class CreateRoomResponse(BaseModel):
    room_id: str

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
            if "글자" in rec_name:
                supp_domains.append(("word", "letter"))
                supp_domains.append(("word", "regular_word"))
        
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
    <title>교사용 스마트 채점 패널 (Multi-Room Teacher Panel)</title>
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
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; box-sizing: border-border-box; }
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
        <div>🔍 국립특수교육원 기초학습기능검사 스마트 채점 패널</div>
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
                <label>아동 학년 (만 나이)</label>
                <select id="select-grade">
                    <option value="유치원">유치원 (만 5세)</option>
                    <option value="초등학교 1학년" selected>초등학교 1학년 (만 6세)</option>
                    <option value="초등학교 2학년">초등학교 2학년 (만 7세)</option>
                    <option value="초등학교 3학년">초등학교 3학년 (만 8세)</option>
                    <option value="초등학교 4학년">초등학교 4학년 (만 9세)</option>
                    <option value="중학교 1학년">중학교 1학년 (만 12세)</option>
                    <option value="고등학교 1학년">고등학교 1학년 (만 15세)</option>
                </select>
            </div>
            <div class="form-group">
                <label>대상별 진단 모듈 선택 (프리셋)</label>
                <select id="select-preset">
                    <option value="1" selected>1. 초1 (기초 해독 & 문해력 스크리닝 모드)</option>
                    <option value="2">2. 초3 발달지체 재심의 (결손 보완 분기 모드)</option>
                    <option value="3">3. 중입 (초6~중1 교과 문해력 진단 모드)</option>
                    <option value="4">4. 고입 (~중3 전환기 기능적 평가 모드)</option>
                </select>
            </div>
            <button onclick="startSession()" style="width:100%; font-size:1.2rem; padding:15px;">🚀 아동용 패널 연동 및 검사 시작</button>
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
            <h1 style="color:#10b981; margin-top:0; text-align:center;">📊 진단평가 결과 및 IEP 권고 리포트</h1>
            <div style="background-color:#f1f5f9; padding:15px; border-radius:8px; margin-bottom:20px;">
                <h3 style="margin-top:0; color:#334155;">피평가자 인적사항</h3>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">
                    <div>👤 <strong>이름:</strong> <span id="rep-name"></span></div>
                    <div>🎒 <strong>학년:</strong> <span id="rep-grade"></span></div>
                    <div>📑 <strong>프리셋:</strong> <span id="rep-preset"></span></div>
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
                <h3 style="margin-top:0; color:#d97706;">⚠️ 보완 진단검사 실시 추천</h3>
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

        function initRoom() {
            if (!currentRoomId) {
                createNewRoom();
            } else {
                updatePinDisplay(currentRoomId);
                pollState();
            }
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

                var maxQuestions = 8;
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
                    학생의 검사 결과 학습 결손(80% 미만)이 확인되었습니다.<br>
                    <strong>특수교육 요강의 지능형 분기 지침</strong>에 따라 다음 보완 검사 추가 실시를 강력히 추천합니다:<br>
                    🎁 <strong>추천 보완 검사:</strong> <span style='color:#d97706; font-weight:700;'>${state.supplementary_recommended.join(", ")}</span>
                `;
            } else {
                suppSection.style.display = "none";
            }

            var iepBox = document.getElementById("iep-guideline-box");
            if (lowScoreDetected) {
                iepBox.innerHTML = `
                    <p style="margin-top:0;"><strong>📌 종합 학습지수 진단: 특수교육적 지원 필요</strong></p>
                    <ul>
                        <li><strong>학습환경:</strong> 학생의 기초 문해력 및 어휘력에서 유의미한 지치가 관찰됩니다. 교사 혹은 특수교사와의 일대일 개별화 수업 배치를 적극 고려해 주세요.</li>
                        <li><strong>어휘 중재 전략:</strong> 아동용 시각 카드(이모지, 일러스트)를 동반한 연상 자극 훈련을 통해 실생활 단어와 쓰기 영역을 다감각(Multisensory) 접근으로 설계해 주십시오.</li>
                        <li><strong>읽기 분석:</strong> 읽기 동작 표현 및 단어 해독 3초 타이밍 훈련(자동화 훈련)을 주 3회 15분 이상 매일 지속하는 것이 음운 결손 해소에 가장 효과적입니다.</li>
                    </ul>
                `;
            } else {
                iepBox.innerHTML = `
                    <p style="margin-top:0;"><strong>📌 종합 학습지수 진단: 정상 범위 내 발달</strong></p>
                    <ul>
                        <li>현재 프리셋 진단평가 영역에서 아동의 수치적 발달 상태는 정상 발달 수준에 완전히 도달해 있습니다.</li>
                        <li>기초 해독 및 읽기 유창성은 우수하므로, 이후 고급 교과 문해력 향상을 위해 긴 글 어휘력 및 추론 중심의 독해 학습을 지속적으로 권장해 드립니다.</li>
                    </ul>
                `;
            }
        }

        initRoom();
    </script>
</body>
</html>
"""

# 아동용 UI HTML (PIN 입력 창 + 실시간 제시)
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
        .giant-emoji {
            font-size: 10rem;
            margin-bottom: 20px;
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

        <!-- 1. 대기 화면 또는 자동중지 완료시 화면 -->
        <div id="student-waiting" class="waiting-screen" style="display:none;">
            <div class="giant-emoji pulse">📖</div>
            <div class="waiting-text" id="waiting-message">반갑습니다!<br>선생님과 함께 재미있는 공부를 시작해봐요.</div>
        </div>

        <!-- 2. 글자 또는 삽화 자극 화면 -->
        <div id="student-exam" style="display:none;">
            <div id="question-area" class="giant-text"></div>
        </div>

    </div>

    <script>
        var studentRoomId = "";

        // URL 파라미터에서 room 추출 (?room=1234)
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
        <h2>🎒 국립특수교육원 기초학습기능검사 다중방 스마트 연동 시스템</h2>
        <p style="color: #475569; font-size: 1.1rem;">여러 선생님께서 동시에 독립적으로 각자의 아동을 평가하실 수 있습니다.</p>
        
        <div style="margin: 30px auto; max-width: 600px; text-align: left; background: #f8fafc; padding: 30px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; color:#1e3a8a;">📱 접속 안내:</h3>
            <div style="margin-bottom: 20px;">
                <p><strong>1. 교사 채점용 패널:</strong></p>
                <a href="/teacher" style="display:inline-block; background:#2563eb; color:white; padding:12px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">📱 교사용 화면 바로가기 (새 방 생성)</a>
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
