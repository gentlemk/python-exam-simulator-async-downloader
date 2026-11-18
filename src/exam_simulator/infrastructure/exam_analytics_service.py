from  .exam_statistics_storage import ExamStatisticsStorage
from time import perf_counter
from domain import Student
import uuid



class ExamAnalyticsService:
    def __init__(self, storage: ExamStatisticsStorage) -> None:
        self.storage = storage

    def update_this_time(self) -> None:
        """
        Обновить текущее время
        """
        with self.storage.lock:
            self.storage.this_time_ms.value = perf_counter()

    def set_correct_answer_question(self, questions_id) -> None:
        """
        Увеличивает счетчик правильных ответов на вопрос
        """
        with self.storage.lock:
            self.storage.question_statistics[questions_id]["correct_answers"] += 1

    def set_total_answer_question(self, questions_id) -> None:
        """
        Увеличивает счетчик ответов на вопрос
        """
        with self.storage.lock:
            self.storage.question_statistics[questions_id]["total_answers"] += 1


    def get_this_time(self) -> float:
        """Получить текущее время"""
        with self.storage.lock:
            return self.storage.this_time_ms.value


    def set_end_time_exam(self, this_time : float) -> None:
        """
        Установить время конца экзамена
        """
        with self.storage.lock:
            self.storage.exam_end_time_ms.value = this_time - self.storage.exam_start_time_ms.value

    def get_time_start_exam(self) -> float:
        """
        Получить время начала экзамена
        """
        with self.storage.lock:
            return self.storage.exam_start_time_ms.value

    def start_time_exam(self) -> None:
        """
        Установить время старта экзамена
        """
        with self.storage.lock:
            self.storage.exam_start_time_ms.value = perf_counter()

    def get_count_students_in_queue(self) -> int:
        """
        Получить количество студентов оставшихся в очереди
        """
        with self.storage.lock:
            return self.storage.count_students_in_queue.value

    def change_status_student(self, student_id, status: Student.Status) -> None:
        """
        Изменяет статус студента, одновременно подсчитывая оставшихся студентов в очереди
        """
        with self.storage.lock:
            old_status = self.storage.student_statistics[student_id]["status"]
            self.storage.student_statistics[student_id]["status"] = status.value
            if old_status == Student.Status.WAITING.value and status != Student.Status.WAITING.value:
                self.storage.count_students_in_queue.value -= 1
            elif old_status != Student.Status.WAITING.value and status == Student.Status.WAITING.value:
                self.storage.count_students_in_queue.value += 1

    def change_current_student_for_examiner(self, examiner_id, student_name: str = '-') -> None:
        """
        Устанавливает какого студента сейчас обслуживает экзаменатор, или значение по умолчанию '-'
        """
        with self.storage.lock:
            self.storage.examination_statistics[examiner_id]["current_student"] = student_name

    def change_exam_time_examiner(self, examiner_id, this_time : float) -> None:
        """
        Устанавливает сколько прошло времени с момента начала экзамена до его завершения у текущего экзаменатора
        """
        with self.storage.lock:
            if self.storage.examination_statistics[examiner_id]["is_finished"]:
                self.storage.examination_statistics[examiner_id]["time_exam"] = this_time - self.storage.exam_start_time_ms.value

    def set_time_exam_student(self, student_id, time_start_answer : float, time_end_answer : float) -> None:
        """Установить время ответа на экзамен студента"""
        with self.storage.lock:
            self.storage.student_statistics[student_id]["time_exam"] = time_end_answer - time_start_answer

    def add_count_served_student(self, examiner_id)-> None:
        """
        Увеличивает счетчик количества студентов которые сдали экзамен текущему экзаменатору
        """
        with self.storage.lock:
            self.storage.examination_statistics[examiner_id]["total_students"] += 1

    def add_count_failed_student(self, examiner_id) -> None:
        """
        Увеличивает счетчик количества студентов которые не сдали экзамен текущему экзаменатору
        """
        with self.storage.lock:
            self.storage.examination_statistics[examiner_id]["fail_students"] += 1

    def finished_examiner(self, examiner_id) -> None:
        with self.storage.lock:
            self.storage.examination_statistics[examiner_id]["is_finished"] = True


