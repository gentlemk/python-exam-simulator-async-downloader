import uuid

from enum import Enum
from random import choices, randint, uniform

from domain.question import Question


class Examiner:
    def __init__(self, name : str, gender : str)-> None:
        self.name = name
        self.gender = gender
        self.is_female = gender == 'Ж'
        self.id = uuid.uuid4()
        self.mood = choices(list(self.Mood), [1, 5, 2])[0]
        self.current_student = None
        self.is_had_lunch = False
        self._len_name = len(name)
        self._time_exam = uniform(self.get_len_name() - 1, self.get_len_name() + 1)
        self._time_lunch = uniform(12, 18)
        
    class Mood(Enum):
        BAD = "Плохое"
        NEUTRAL = "Нейтральное"
        GOOD = "Хорошее"

    def __repr__(self) -> str:
        return f'<class Examiner> name:{self.name}; gender:{self.gender}\n'

    def get_time_exam(self) -> float:
        """возвращает время сдачи экзамена"""
        return self._time_exam

    def get_len_name(self) -> int:
        """возвращает длину имени экзаменатора"""
        return self._len_name

    def get_time_lunch(self) -> float:
        """Возвращает время обеда экзаменатора"""
        return self._time_lunch

    def get_answers(self, question : Question) -> list[str]:
        words = question.words.copy()
        answers = []
        answer = question.get_random_word(self.is_female)
        answers.append(answer)
        while randint(1, 3) == 3:
            if answer in words:
                words.remove(answer)
            
            if not words:
                break
            
            answer = question.get_random_word(self.is_female, custom_words=words)
            answers.append(answer)

        return answers

