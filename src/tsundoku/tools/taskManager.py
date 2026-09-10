from tsundoku.models.tasks import Task


class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def addTask(self, task : Task):
        self.tasks.append(task)

    def removeTask(self, task : Task):
        self.tasks.remove(task)

    def getTasks(self):
        return self.tasks   