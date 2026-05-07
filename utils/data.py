from peewee import *
from utils import config


_dbs: dict[str, SqliteDatabase] = {}


def _get_db(lang: str) -> SqliteDatabase:
    if lang not in _dbs:
        _dbs[lang] = SqliteDatabase(
            f"{config.Data.path}/{lang}.db",
            pragmas={"journal_mode": "wal", "foreign_keys": 1},
        )
    return _dbs[lang]


class _Create:
    @staticmethod
    def data(lang: str) -> type[Model]:
        db = _get_db(lang)

        class Data(Model):
            id = IntegerField(primary_key=True)
            name = CharField()
            price = CharField()
            theme = CharField()
            sale_infos = CharField()
            rating = FloatField()
            pieces = IntegerField()
            ages = CharField()
            image = TextField()
            logo = TextField()
            url = TextField()

            class Meta:
                database = db

        db.create_tables([Data], safe=True)
        return Data

    @staticmethod
    def page(lang: str) -> type[Model]:
        db = _get_db(lang)

        class Page(Model):
            id = IntegerField(default=1, primary_key=True)
            page = IntegerField(default=1)

            class Meta:
                database = db

        db.create_tables([Page], safe=True)
        return Page


class Page:
    def __init__(self, lang: str):
        self.lang = lang or "en-us"
        self._model = _Create.page(self.lang)

    def get(self) -> int:
        obj, _ = self._model.get_or_create(id=1, defaults={"page": 1})
        return obj.page

    def set(self, page: int) -> None:
        self._model.update(page=page).where(self._model.id == 1).execute()


class Data:
    def __init__(self, lang: str):
        self.lang = lang or "en-us"
        self._model = _Create.data(self.lang)

    def get_by_id(self, id: int) -> Model | None:
        return self._model.get_or_none(id=id)

    def is_set_exist(self, id: int) -> bool:
        return self._model.get_or_none(id=id) is not None

    def add_set(self, force: bool = False, **kwargs) -> bool:
        try:
            self._model.create(**kwargs)
            return True
        except IntegrityError:
            if not force:
                return False
            try:
                self._model.update(**kwargs).where(
                    self._model.id == kwargs.get("id")
                ).execute()
                return True
            except Exception as e:
                print(f"[Data] update failed (id={kwargs.get('id')}): {e}")
                return False
