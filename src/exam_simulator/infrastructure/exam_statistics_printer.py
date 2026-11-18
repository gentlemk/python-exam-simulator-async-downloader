import os
from multiprocessing.managers import DictProxy
import prettytable as pt
from time import sleep

from application.result_analyzer import ExamResultAnalyzer
from infrastructure.exam_analytics_service import ExamAnalyticsService


class ExamStatisticsPrinter:
    @staticmethod
    def clear_terminal() -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def __init__(self):
        self.students_table = pt.PrettyTable(["Студент", "Статус"])
        self.students_table.align["Студент"] = "l"
        self.examiners_table = pt.PrettyTable(["Экзаменатор", "Текущий студент", "Всего студентов", "Завалил", "Время работы"])
        self.examiners_table.align["Экзаменатор"] = "l"
        self.examiners_table.align["Текущий студент"] = "l"

    def print_student_statistics(self, student_statistics: DictProxy):
        """
        Печатает таблицу с информацией о студентах
        """
        self.students_table.clear_rows()
        priority = {"Очередь" : 0, "Сдал" : 1, "Провалил" : 2}
        for studentID in student_statistics:
            self.students_table.add_row([student_statistics[studentID]["name"], student_statistics[studentID]["status"]])
        self.students_table.sortby = "Статус"
        self.students_table.sort_key = lambda row: priority[str(row[2])]
        print(self.students_table)

    def print_examiner_statistics(
            self,
            examiner_statistics: DictProxy,
            start_exam: float,
            this_time : float,
    ) -> None:
        """
        Печатает таблицу с информацией об экзаменаторах в момент экзамена
        """
        self.examiners_table.clear_rows()
        for examinerID in examiner_statistics:
            if examiner_statistics[examinerID]["is_finished"]:
                work_time = examiner_statistics[examinerID]["time_exam"]
            else:
                work_time = this_time - start_exam
            self.examiners_table.add_row([
                examiner_statistics[examinerID]["name"],
                examiner_statistics[examinerID]["current_student"],
                examiner_statistics[examinerID]["total_students"],
                examiner_statistics[examinerID]["fail_students"],
                ExamStatisticsPrinter.get_format_time(work_time)
            ])
        print(self.examiners_table)

    @staticmethod
    def get_format_time(count_ms):
        """
        Получить время в формате ss.mm
        s - секунды m - миллисекунды
        """
        seconds = int(count_ms)
        milliseconds = int((count_ms - seconds) * 100)
        return f"{seconds:d}.{milliseconds:02d}"

    @staticmethod
    def print_current_statistics(
            count_queue_student : int,
            count_all_student : int,
            count_ms_from_start_exam : float,
    ) -> None:
        """
        Выводит текст с информацией сколько осталось студентов в очереди и сколько прошло времени
        """
        print(f"Осталось в очереди студентов: {count_queue_student} из {count_all_student}")
        print(f"Время с момента начала экзамена: {ExamStatisticsPrinter.get_format_time(count_ms_from_start_exam)}")

    def print_state_exam(
            self,
            analytics_service : ExamAnalyticsService,
            storage_students: DictProxy,
            storage_examiners: DictProxy,
    ) -> None:
        """
        Печатает статистику во время экзамена
        """
        analytics_service.update_this_time()
        self.print_student_statistics(storage_students)
        print()
        self.print_examiner_statistics(
            storage_examiners,
            analytics_service.get_time_start_exam(),
            analytics_service.get_this_time(),
        )
        print()
        self.print_current_statistics(
            analytics_service.get_count_students_in_queue(),
            len(storage_students),
            analytics_service.get_this_time() - analytics_service.get_time_start_exam(),
        )
        sleep(0.5)
        ExamStatisticsPrinter.clear_terminal()

    def print_finished_examiner_statistics(self,) -> None:
        """
        Печатает таблицу экзаменаторов после сдачи экзамена
        """
        finished_table = self.examiners_table
        finished_table.del_column("Текущий студент")
        print(finished_table)

    def print_finished_state(
            self,
            storage_students: DictProxy,
            result_analyzer: ExamResultAnalyzer,
    ) -> None:
        """
        Печатает таблицу со статистикой после завершения экзамена
        """
        self.print_student_statistics(storage_students)
        print()
        self.print_finished_examiner_statistics()
        print()
        self.print_last_text(result_analyzer)

    def print_last_text(
            self,
            analyzer : ExamResultAnalyzer,
    ) -> None:
        print(f"Время с момента начала экзамена и до момента его завершения: {self.get_format_time(analyzer.get_max_time_work_examiner())}")
        print(f"Имена лучших студентов: {', '.join(analyzer.get_name_best_students())}")
        print(f"Имена лучших экзаменаторов: {', '.join(analyzer.get_name_best_examiner())}")
        print(f"Имена студентов, которых после экзамена отчислят: {', '.join(analyzer.get_names_students_who_expelled())}")
        print(f"Лучшие вопросы: {', '.join(analyzer.get_best_questions())}")
        if analyzer.get_result_exam():
            print("Вывод: экзамен удался")
        else:
            print("Вывод: экзамен не удался")

