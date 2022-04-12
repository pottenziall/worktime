
@dataclass
class WorkDay:
    start: str
    end: str
    pauses: typing.List = field(default_factory=list)

    def add_pause(self, pause: str):
        self.pauses.append(pause)

TABLE_COLUMNS = {"date": 300, "start": 300, "end": 300, "pause": 200}
