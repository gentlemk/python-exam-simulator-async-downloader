from enum import Enum
from domain.question import Question
import uuid


class Student:
    def __init__(self, name: str, gender: str):
        self.name = name
        self.gender = gender
        self.is_female = gender == 'Ж'
        self.status = self.Status.WAITING
        self.id = uuid.uuid4()

    class Status(Enum):
        WAITING = "Очередь"
        PASSED = "Сдал"
        FAILED = "Провалил"

    def __repr__(self):
        return f'<class Student> name:{self.name}; gender:{self.gender}; ID:{self.id}>; status:{self.status}'

    def get_answer(self, question: Question) -> str:
        return question.get_random_word(self.is_female)