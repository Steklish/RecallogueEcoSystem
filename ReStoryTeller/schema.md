categories = [
    "Политика",
    "Экономика", 
    "Спорт",
    "Технологии",
    "Культура",
    "Общество",
    "Мир",
    "Наука",
    "Здоровье",
    "Бизнес",
    "Образование",
    "Экология",
    "Криминал",
    "Армия",
    "Шоу-бизнес"
]

Доступные категории: Политика, Экономика, Спорт, Технологии, Культура, Общество, Мир, Наука, Здоровье, Бизнес, Образование, Экология, Криминал, Армия, Шоу-бизнес.



PREFETCHER is crucial for my project. SO i have to make it. O(n^2) nica and all but im gonna make it different.
- for entities with spacy
- for topics with ChromaDB

Graph hirearchy:
- category -> a simple tag that is used for filtering
- topic -> is an event described in a article 
- article (connected to topic)
- entity (has relationships with the other entitties)
- relationship (topic and category tag)
