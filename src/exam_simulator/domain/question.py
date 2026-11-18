import uuid

from random import choices

# Золотое сечение
PHI = (1 + 5 ** 0.5) / 2

class Question:
    def __init__(self, text : str):
        self.text = text.strip()
        self.words = self.text.split()
        self.count_words = len(self.text)
        self.id = uuid.uuid4()

    def __repr__(self):
        return f'<Question text: {self.text}>\n'
    
    def get_random_word(self, is_female: bool, custom_words: list[str] | None = None) -> str:
        """
        Выбирает случайное слово из вопроса по закону золотого сечения.
        Учитывает пол (мальчики выбирают ближе к началу, девочки — к концу).
        """
        target_words = custom_words if custom_words is not None else self.words
        probabilities = self._make_probability(len(target_words))

        if is_female:
            probabilities.reverse()

        answer = choices(target_words, weights=probabilities, k=1)
        return answer[0]
    

    @staticmethod
    def _make_probability(count_words: int) -> list[float]:
        """
        Генерирует список вероятностей для слов по закону золотого сечения.
        Сумма вероятностей всегда равна 1.0.
        """
        
        if count_words == 0:
            raise ValueError("Список слов в вопросе не может быть пустым.")

        probabilities = []
        remainder = 1.0

        for _ in range(count_words - 1):
            p = remainder / PHI
            probabilities.append(p)
            remainder -= p
            
        probabilities.append(remainder)

        return probabilities
