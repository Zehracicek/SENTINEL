"""Test ortamı hazırlığı.

`database.py` import anında DATABASE_URL bekliyor (tanımsızsa RuntimeError).
Testler veritabanına bağlanmaz; yalnızca import zincirini geçebilmek için
sahte bir bağlantı dizesi tanımlanır. Bu, gerçek `.env` dosyası testleri
etkilemesin diye de gereklidir.
"""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
)
os.environ.setdefault(
    "DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/test_db"
)
# Groq çağrısı asla yapılmasın
os.environ.pop("GROQ_API_KEY", None)
