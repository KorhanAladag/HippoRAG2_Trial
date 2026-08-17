# Satır Satır Kod Rehberi

Bu belge projedeki her Python satırını numarasıyla birlikte açıklıyor.
Önceki rehber genel bir bakıştı, bu ise gerçekten satır satır.

Okurken kodu yanına açık tut, satır numaraları birebir uyuşuyor.

## İçindekiler

1. [settings.py](#settingspy) (279 satır)
2. [check_config.py](#check_configpy) (21 satır)
3. [hippo_factory.py](#hippo_factorypy) (92 satır)
4. [index.py](#indexpy) (111 satır)
5. [stats.py](#statspy) (88 satır)
6. [query.py](#querypy) (82 satır)
7. [test_identifiers.py](#test_identifierspy) (61 satır)
8. [test_revision.py](#test_revisionpy) (84 satır)

---

# settings.py

Projenin omurgası. Ayarları okur, tipler, doğrular. HippoRAG'i hiç bilmez.

## Satır 1-23: Modül docstring

```python
"""
Application settings, loaded from the environment.
...
"""
```

Üç tırnak arasındaki metin **docstring**. Dosyanın en başında olduğu için
modül docstring'i sayılıyor ve `help(settings)` yazdığında bu görünüyor.
Yorum satırı (`#`) ile farkı: docstring çalışma anında erişilebilir bir
string nesnesi, yorum ise derleme sırasında atılıyor.

İçerik üç soruyu cevaplıyor: neden `.env` dosyası var, neden dağınık
`os.getenv` yerine bir sınıf var, neden üretimde `.env` okunmuyor. Bu
soruların cevabı koda bakarak anlaşılmaz, o yüzden yazılı olmalı.

## Satır 25: Gelecekten import

```python
from __future__ import annotations
```

Tip ipuçlarının çalışma anında değil, sadece metin olarak saklanmasını
sağlıyor. İki faydası var. Birincisi `list[str]` gibi modern yazımları eski
Python sürümlerinde kullanabilmek. İkincisi henüz tanımlanmamış bir sınıfa
tip olarak atıf yapabilmek, mesela `def load(cls) -> "Settings"` içindeki
`Settings` henüz oluşmamış olsa bile.

Bu satır her zaman dosyanın en üstünde, docstring'den hemen sonra olmak
zorunda. Başka bir import'tan sonra gelirse Python hata verir.

## Satır 27-30: Standart kütüphane importları

```python
import os
import sys
from dataclasses import dataclass
from typing import Literal, Optional
```

`os` ortam değişkenlerini okumak için (`os.getenv`).

`sys` hata mesajlarını `stderr`'e yazmak için. Normal çıktı `stdout`'a,
hatalar `stderr`'e gider; böylece `python index.py > log.txt` yazdığında
hatalar ekranda kalır, log dosyasına karışmaz.

`dataclass` sınıf tanımını kısaltan bir dekoratör. Normalde `__init__`,
`__repr__`, `__eq__` metodlarını elle yazman gerekir, bu onları otomatik
üretir.

`Literal` bir değerin sadece belirli seçeneklerden biri olabileceğini
söylüyor. `Optional[str]` ise "string ya da None" demek, `Union[str, None]`
ile aynı şey.

Bu importların standart kütüphaneden geldiğine dikkat et: hiçbiri
`pip install` gerektirmiyor.

## Satır 32: Üçüncü parti import

```python
from dotenv import load_dotenv
```

`python-dotenv` paketinden geliyor, yani `requirements.txt`'te olması
gerekiyor. Python'un import konvansiyonu şu sırayı ister: önce standart
kütüphane, sonra üçüncü parti, sonra kendi modüllerin. Aralarında boş satır
olur. Bu dosyada 27-30 standart, 32 üçüncü parti.

## Satır 34-36: .env dosyasını yükle

```python
# override=False is deliberate. Real environment variables always win over the
# file, which is what lets the same image run in development and production.
load_dotenv(override=False)
```

Bu satır `.env` dosyasını bulup içindeki değerleri `os.environ`'a yüklüyor.

`override=False` projedeki en önemli tek parametre. Anlamı: **zaten tanımlı
olan bir ortam değişkeni varsa dosyadaki değer onu ezmesin.**

Neden önemli: Docker konteynerinde veya systemd altında `.env` dosyası yoktur,
değişkenler platform tarafından enjekte edilir. `override=True` olsaydı ve
bir şekilde `.env` dosyası da bulunsaydı, dosya platformun verdiği gerçek
değerleri ezerdi. `override=False` ile aynı kod hem laptopta hem üretimde
doğru çalışıyor.

Bu satırın modül seviyesinde, yani bir fonksiyonun içinde değil, doğrudan
dosyada olması da bilinçli: import edildiği anda çalışıyor, yani aşağıdaki
`_str` ve `_int` çağrıları `.env` yüklenmiş halde buluyor.

## Satır 39-40: Özel hata sınıfı

```python
class ConfigError(RuntimeError):
    """Raised when the configuration cannot produce a working application."""
```

`RuntimeError`'dan türeyen bir hata tipi. Gövdesi sadece bir docstring, çünkü
ek koda ihtiyacı yok.

Neden var: `except ConfigError` yazabilmek için. Eğer düz `RuntimeError`
kullansaydık, `except RuntimeError` yazdığımızda konfigürasyon hatalarıyla
birlikte koddaki gerçek buglar da yakalanırdı ve ikisini ayıramazdık.

Sınıf gövdesinin docstring'den ibaret olması Python'da geçerli, çünkü
docstring bir ifade sayılıyor. Alternatif olarak `pass` yazılabilirdi ama
docstring hem gövde görevi görüyor hem de belgeliyor.

## Satır 43-46: Yardımcı fonksiyonlar bölümü yorumu

```python
# --- typed readers ---------------------------------------------------------
# Every value arrives from the environment as a string. These helpers convert
# and fail loudly, naming the variable, rather than raising a bare ValueError
# from somewhere deep in the call stack.
```

Bölüm ayracı. Uzun dosyalarda gezinmeyi kolaylaştırıyor. Tirelerle satır sonuna
kadar uzatılması yaygın bir konvansiyon, editörde göz yakalıyor.

## Satır 48-49: Metin okuyucu

```python
def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()
```

Fonksiyon adının alt çizgiyle başlaması Python'da "bu modüle özel, dışarıdan
kullanma" anlamına gelen bir konvansiyon. Zorlayıcı değil, sadece niyet
bildirimi.

`os.getenv(name, default)` değişken yoksa `default` döndürüyor.

`.strip()` baştaki ve sondaki boşlukları kırpıyor. Bu küçük detay önemli:
`.env` dosyasında `SAVE_DIR = outputs` yazarsan (eşittirin etrafında boşlukla)
değer `" outputs"` olarak gelir ve klasör adı yanlış olur.

Tip ipuçları (`name: str`, `-> str`) çalışma anında hiçbir şey yapmıyor, ama
editörün otomatik tamamlaması ve `mypy` gibi araçlar için değerli.

## Satır 52-55: Opsiyonel değer okuyucu

```python
def _opt(name: str) -> Optional[str]:
    """Empty string and unset both mean 'not configured'."""
    value = os.getenv(name, "").strip()
    return value or None
```

`_str`'den farkı: boş değeri `None`'a çeviriyor.

`return value or None` ifadesi Python'un "truthy" mantığını kullanıyor. Boş
string `False` sayıldığı için, `value` boşsa `or` ifadesi `None` döndürüyor;
doluysa `value`'yu döndürüyor.

Neden gerekli: `.env` dosyasında `QDRANT_API_KEY=` yazmak "anahtar yok"
demektir, ama `os.getenv` bunu boş string olarak döndürür. Boş string ile
`None` arasındaki fark ilerideki kontrollerde önemli: `if self.qdrant_api_key`
kontrolü ikisinde de `False` verir ama `None` niyeti daha net anlatır.

## Satır 58-65: Tamsayı okuyucu

```python
def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
```

Satır satır:

**59:** Ham değeri oku ve kırp.

**60-61:** Boşsa varsayılanı döndür. `if not raw` ifadesi hem boş string hem
de sadece boşluk içeren durumu yakalıyor (çünkü `.strip()` sonrası boş kalır).

**62-63:** Sayıya çevirmeyi dene.

**64:** `ValueError` yakala. Bu, `int("abc")` çağrısının fırlattığı hata.

**65:** Kendi hatamıza çevir. İki detay önemli:

`{raw!r}` ifadesindeki `!r` `repr()` çağırıyor, yani değeri tırnak içinde
gösteriyor. `got abc` yerine `got 'abc'` yazıyor. Fark şurada: değer
`"5 "` gibi görünmez bir boşluk içeriyorsa `!r` bunu görünür kılıyor.

`from exc` orijinal hatayı zincire ekliyor. Traceback'te "yukarıdaki hata
şuna yol açtı" şeklinde iki hata birden görünüyor. Hata ayıklarken hangi
dönüşümün patladığını gösteriyor.

## Satır 68-75: Ondalık okuyucu

`_int` ile birebir aynı yapı, sadece `int` yerine `float` ve mesajda
"integer" yerine "number". `SYNONYMY_THRESHOLD` gibi 0.8 değerleri için.

Neden ikisi ayrı: `float("5")` çalışır ve 5.0 döndürür, yani tek fonksiyonla
idare edilebilirdi. Ama o zaman `QA_TOP_K=5.7` yazan biri hata almazdı, 5.7
passage istemiş olurdu ki anlamsız. Ayrı tutmak bunu yakalıyor.

## Satır 78: Dataclass dekoratörü

```python
@dataclass(frozen=True)
```

`@` işaretiyle başlayan satır bir **dekoratör**. Altındaki sınıfı alıp
değiştirilmiş halini geri veriyor.

`dataclass` şunları otomatik üretiyor:
- `__init__`: alan tanımlarından yola çıkarak kurucu metod
- `__repr__`: `print(settings)` yazdığında okunabilir çıktı
- `__eq__`: iki nesneyi alanlarına göre karşılaştırma

`frozen=True` ise nesneyi **değiştirilemez** yapıyor. Kurulduktan sonra
`settings.qa_top_k = 10` yazarsan hata alırsın.

Neden isteniyor: konfigürasyon programın ortasında değişmemeli. Değişebilseydi
"acaba bu değer nerede değişti" tipi hataları ayıklamak zorunda kalırdın.
Bu satır o hata sınıfını tamamen ortadan kaldırıyor.

## Satır 79-85: Sınıf tanımı ve docstring

```python
class Settings:
    """
    Every value the application reads, resolved once.

    frozen=True means nothing can reassign a setting halfway through a run,
    which removes a whole class of confusing bugs.
    """
```

Sınıf docstring'i. Dekoratörün ne yaptığını burada da açıklamak faydalı,
çünkü `@dataclass(frozen=True)` satırını görmeyen biri sınıfın içine bakar.

## Satır 87-120: Alan tanımları

```python
    # environment
    app_env: Literal["development", "staging", "production"]
    log_level: str

    # models
    llm_base_url: str
    ...
```

Bunlar `dataclass` için alan tanımları. Değer atanmadığı için hepsi
**zorunlu** parametre oluyor, yani `Settings()` çağrısında hepsi verilmeli.

Neden varsayılan değer verilmedi: varsayılanlar `load()` metodunda, ortam
değişkeni okunurken uygulanıyor. İki yerde varsayılan olsaydı hangisinin
geçerli olduğu karışırdı.

`Literal["development", "staging", "production"]` sadece bu üç değerden
birinin geçerli olduğunu söylüyor. Ama dikkat: bu **çalışma anında zorlanmıyor**.
`mypy` gibi statik analiz araçları yakalar, Python kendisi yakalamaz. Gerçek
kontrol satır 163'te, `validate()` içinde yapılıyor.

Yorum satırlarıyla gruplandırma (`# environment`, `# models`, `# vector store`)
yirmi alanı okunabilir tutuyor.

## Satır 122-124: Sınıf metodu başlangıcı

```python
    # ---------------------------------------------------------------
    @classmethod
    def load(cls) -> "Settings":
```

`@classmethod` dekoratörü metodun nesneye değil sınıfa ait olduğunu söylüyor.
İlk parametre `self` yerine `cls` ve bu, sınıfın kendisi.

Neden classmethod: bu metod bir nesne üretiyor, yani çağrıldığında henüz
nesne yok. `Settings.load()` şeklinde sınıf üzerinden çağrılıyor.

Bu desene **factory method** deniyor: kurucuya alternatif, adlandırılmış bir
nesne üretme yolu.

`-> "Settings"` dönüş tipi tırnak içinde, çünkü satır 124'te sınıf henüz
tanımlanmayı bitirmemiş. Satır 25'teki `from __future__ import annotations`
sayesinde aslında tırnak da gerekmiyordu ama zararı yok ve daha açık.

## Satır 125-149: Ayarları oku

```python
        settings = cls(
            app_env=_str("APP_ENV", "development"),
            log_level=_str("LOG_LEVEL", "INFO").upper(),
            ...
        )
```

`cls(...)` çağrısı `Settings(...)` ile aynı şey. Her alan için ilgili okuyucu
fonksiyon çağrılıyor.

Satır 127'deki `.upper()` dikkat çekici: `.env` dosyasında `LOG_LEVEL=info`
yazan biri de çalışsın diye. Küçük bir hoşgörü, ama kullanıcıya bir hata
mesajı göstermekten iyi.

Satır 129-131'de `embedding_base_url` üç satıra bölünmüş, çünkü varsayılan
değer uzun. Python'da parantez içindeki ifadeler satır sonuna kadar devam
etmek zorunda değil, bu yüzden bölmek serbest.

Bu blok **tek merkez**: yeni bir ayar eklerken sadece burayı, alan
tanımlarını ve `.env.example`'ı güncellersin.

## Satır 150-151: Doğrula ve döndür

```python
        settings.validate()
        return settings
```

Doğrulama nesne kurulduktan **sonra** çağrılıyor, çünkü bazı kontroller
alanlar arası ilişkiye bakıyor (mesela `qa_top_k` ile `retrieval_top_k`
karşılaştırması). Kurulmadan bunu yapamazsın.

`validate()` bir şey döndürmüyor, sorun varsa hata fırlatıyor. Yani bu satır
geçtiyse ayarlar geçerli demektir.

## Satır 154-160: Doğrulama metodu ve docstring

```python
    def validate(self) -> None:
        """
        Fail at startup rather than three hours into an indexing run.

        Every check here corresponds to a mistake that is easy to make and
        expensive to discover late.
        """
```

`-> None` hiçbir şey döndürmediğini söylüyor. Fonksiyonun amacı yan etki
(hata fırlatmak), değer üretmek değil.

## Satır 161: Hata listesi

```python
        problems: list[str] = []
```

Boş bir liste. Bulunacak her sorun buraya eklenecek.

Neden liste, neden ilk hatada durup fırlatmıyoruz: beş hatan varsa beş kez
çalıştırıp beş kez düzeltmek zorunda kalırdın. Hepsini toplayıp bir kerede
göstermek çok daha kullanışlı.

Tip ipucu `list[str]` boş listenin ne tutacağını söylüyor.

## Satır 163-167: Ortam adı kontrolü

```python
        if self.app_env not in {"development", "staging", "production"}:
            problems.append(
                f"APP_ENV must be development, staging or production, "
                f"got {self.app_env!r}"
            )
```

Süslü parantez `{...}` bir **set** oluşturuyor, liste değil. Fark: set'te
üyelik kontrolü (`in`) sabit zamanda, listede doğrusal zamanda. Üç eleman
için önemsiz ama doğru alışkanlık.

İki f-string yan yana yazılmış ve Python bunları otomatik birleştiriyor.
Uzun mesajları satıra sığdırmanın standart yolu.

Bu kontrol satır 88'deki `Literal` tipinin çalışma anındaki karşılığı. Tip
ipucu belgeliyor, bu satır zorluyor.

## Satır 169-173: Vektör deposu kontrolü

Aynı kalıp, bu sefer `vector_store_type` için. Dört geçerli değer HippoRAG'in
kendi kodundan alındı, uydurma değil.

## Satır 175-182: Embedding URL kontrolü

```python
        # The embeddings endpoint has a different path from chat completions.
        # Pointing both at /v1 is a common mistake and produces a confusing
        # 404 halfway through the first batch.
        if self.embedding_base_url.rstrip("/").endswith("/v1"):
            problems.append(
                "EMBEDDING_BASE_URL looks like a chat endpoint. Ollama expects "
                "/v1/embeddings for embeddings."
            )
```

Bu kontrolün varlık sebebi tamamen deneyimsel: Ollama'da sohbet ucu `/v1`,
embedding ucu `/v1/embeddings`. İkisini aynı yazmak çok yapılan bir hata ve
sonucu ilk embedding partisinin ortasında gelen anlamsız bir 404.

`.rstrip("/")` sondaki eğik çizgileri kırpıyor, böylece hem
`http://x/v1` hem `http://x/v1/` yakalanıyor.

Not: bu bir **sezgisel** kontrol, kesin değil. Ollama dışında bir sağlayıcı
kullanırsan yanlış alarm verebilir. O durumda kontrolü gevşetmek gerekir.

## Satır 184-188: Eşik aralığı kontrolü

```python
        if not 0.0 < self.synonymy_threshold < 1.0:
            problems.append(
                f"SYNONYMY_THRESHOLD is a cosine similarity and must sit "
                f"between 0 and 1, got {self.synonymy_threshold}"
            )
```

`0.0 < x < 1.0` yazımı Python'a özel bir kolaylık: matematikteki gibi zincir
karşılaştırma yapabiliyorsun. Çoğu dilde `x > 0.0 && x < 1.0` yazman gerekir.

Başındaki `not` ifadeyi tersine çeviriyor: "aralıkta değilse sorun var".

Kosinüs benzerliği tanım gereği -1 ile 1 arasında, embedding'ler normalize
edilmişse 0 ile 1 arasında. 1.5 gibi bir değer hiçbir kenar üretmez ve graf
tamamen boş çıkar, ama hata da vermez. Sessiz başarısızlık, bu yüzden kontrol.

## Satır 190-195: Mantıksal tutarlılık kontrolü

```python
        if self.qa_top_k > self.retrieval_top_k:
```

Alanlar arası ilişki kontrolü. Getirilenden fazla passage'la cevap veremezsin.

Bu kontrolün ayrı bir değeri var: tek başına bakıldığında iki değer de
geçerli. Sorun ancak birlikte bakınca görünüyor. `validate()` metodunun
kurucudan sonra çağrılmasının sebebi tam olarak bu.

## Satır 197-201: Chunk örtüşme kontrolü

Örtüşme parça boyutundan büyük veya eşitse chunking mantığı bozulur: her
parça bir öncekini tamamen kapsar ve sonsuz döngüye benzer bir durum oluşur.

## Satır 203-223: Üretim kuralları

```python
        # Production only rules. These would be annoying on a laptop and are
        # non negotiable on a shared machine.
        if self.app_env == "production":
```

Bu blok sadece `APP_ENV=production` iken çalışıyor. Fikir şu: geliştirme
ortamında esneklik iyi, üretimde katılık iyi.

**206-211:** Parquet backend reddediliyor. Gerekçe mesajda yazılı: passage
başına 0,85 MB. Bu, projede aldığımız en önemli kararın koda gömülmüş hali.

**212-217:** Uzak sunucuya düz `http` ile bağlanmak reddediliyor. `localhost`
istisna tutulmuş, çünkü yerel trafik ağa çıkmıyor.

Satır sonundaki `\` işareti ifadenin bir sonraki satırda devam ettiğini
söylüyor. Koşul iki satıra sığmadığı için gerekli.

**218-223:** Uzak Qdrant'a şifresiz bağlanmak reddediliyor. Kimlik doğrulaması
olmayan bir vektör veritabanı, verinin herkese açık olması demek.

## Satır 225-228: Hataları fırlat

```python
        if problems:
            raise ConfigError(
                "Configuration is not usable:\n  - " + "\n  - ".join(problems)
            )
```

`if problems` boş liste `False` sayıldığı için "en az bir sorun varsa"
anlamına geliyor.

`"\n  - ".join(problems)` listeyi tek bir metne çeviriyor, aralarına satır
sonu ve tire koyarak. Sonuç şöyle görünüyor:

```
Configuration is not usable:
  - APP_ENV must be development, staging or production, got 'prod'
  - QA_TOP_K (500) cannot exceed RETRIEVAL_TOP_K (200)
```

Okunabilirlik önemli, çünkü bu mesajı okuyan kişi muhtemelen aceleci ve
sinirli.


## Satır 231-241: Özet metodu ve maskeleme

```python
    def describe(self) -> str:
        """
        Human readable summary, with secrets masked.
        ...
        """
        def mask(value: Optional[str]) -> str:
            if not value:
                return "(not set)"
            return f"{value[:4]}...{value[-2:]}" if len(value) > 8 else "(set)"
```

Satır 238'de fonksiyon içinde fonksiyon tanımlanmış. Buna **iç içe fonksiyon**
deniyor ve sadece `describe` içinde görünür. Başka yerde kullanılmayacak bir
yardımcı için doğru yer burası; modül seviyesine koymak isim alanını
kirletirdi.

`mask` mantığı: değer yoksa "(not set)", 8 karakterden uzunsa ilk dört ve son
iki karakter arası noktalarla, kısaysa sadece "(set)".

Neden kısa değerler tamamen gizleniyor: dört karakterlik bir anahtarın ilk
dördünü göstermek anahtarın tamamını göstermek olurdu.

Neden hiç göstermiyoruz demiyoruz: kısmi gösterim "doğru anahtarı mı
kullanıyorum" sorusunu cevaplamaya yetiyor, ama anahtarı kopyalamaya yetmiyor.
Loglarda tam da bu isteniyor.

## Satır 243-257: Özet metnini kur

```python
        return "\n".join([
            f"environment    : {self.app_env}",
            f"extraction     : {self.extraction_model}",
            ...
        ])
```

Liste kurup `"\n".join` ile birleştirmek, art arda `+=` yapmaktan hem hızlı
hem okunaklı. Python'da string değiştirilemez olduğu için her `+=` yeni bir
nesne yaratır.

Alan adlarının boşluklarla hizalanması (`environment    :`) çıktının tablo
gibi okunmasını sağlıyor. Küçük detay ama günde on kez bakacağın bir çıktı.

Satır 250-251 ilginç: tek bir liste elemanı iki f-string'e bölünmüş, çünkü
satıra sığmıyor. Python bunları otomatik birleştiriyor, yani listede tek bir
eleman olarak duruyorlar.

`{self.qdrant_url or 'local file'}` ifadesi Qdrant URL'i yoksa "local file"
yazıyor. Kullanıcıya boş bir alan göstermek yerine ne olduğunu anlatıyor.

## Satır 260-274: Yükle veya çık

```python
def _load_or_exit() -> Settings:
    """
    Load settings and turn a ConfigError into a clean message.

    A traceback is right for a bug in the code and wrong for a typo in a
    config file. The person who mistyped a variable needs to read one line,
    not twenty.
    """
    try:
        return Settings.load()
    except ConfigError as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        print("Copy .env.example to .env and correct the values above.",
              file=sys.stderr)
        raise SystemExit(1)
```

Docstring'deki gerekçe önemli: traceback koddaki bir bug için doğru araç,
config dosyasındaki yazım hatası için yanlış. Değişken adını yanlış yazan
kişi yirmi satırlık yığın izi değil, bir satır okumak istiyor.

`file=sys.stderr` çıktıyı hata akışına yönlendiriyor. Böylece
`python index.py > log.txt` yazıldığında hata ekranda kalıyor.

`raise SystemExit(1)` programı 1 çıkış koduyla sonlandırıyor. Sıfır olmayan
kod "başarısız" demek ve bu, kabuk betikleri ile CI sistemleri için önemli:
`python check_config.py && python index.py` yazdığında ilki başarısızsa
ikincisi hiç çalışmıyor.

`sys.exit(1)` de aynı işi yapardı, ikisi de aynı istisnayı fırlatıyor.

## Satır 277-279: Modül seviyesinde yükleme

```python
# Loaded once at import. Every module does `from settings import settings`,
# so there is exactly one resolved configuration per process.
settings = _load_or_exit()
```

Dosyanın son satırı ve en önemlilerinden biri.

Bu satır **import anında** çalışıyor. Yani `from settings import settings`
yazan her dosya, ayarların yüklenmiş ve doğrulanmış halini buluyor.

Python modülleri bir kez import ediyor ve sonuçları önbelleğe alıyor. Bu
yüzden beş dosya `from settings import settings` yazsa bile `_load_or_exit`
yalnızca bir kez çalışıyor. Süreç başına tam olarak bir konfigürasyon var.

Bu desene **modül seviyesi singleton** deniyor. Alternatifleri var (sınıf
seviyesi singleton, dependency injection) ama bu boyuttaki bir proje için
en sade olanı bu.

Yan etkisi: geçersiz bir `.env` ile herhangi bir betiği çalıştırdığında,
o betik tek satır kendi kodunu çalıştırmadan hata veriyor. İstenen davranış
tam olarak bu.

---

# check_config.py

Yirmi bir satır, ama işlevi büyük: hiçbir servise dokunmadan ayarları
doğruluyor.

## Satır 1-8: Docstring

Ne yaptığını ve neden var olduğunu söylüyor: yeni bir makinede ilk
çalıştırılacak şey, bir saniyede hata verir.

## Satır 10: Tek import

```python
from settings import settings
```

Bu satır tek başına tüm doğrulamayı tetikliyor. `settings.py` dosyasının son
satırı (`settings = _load_or_exit()`) import anında çalıştığı için, ayarlar
geçersizse program buraya bile gelmiyor.

Yani dosyanın asıl işi bu satırda bitiyor, geri kalanı sadece çıktı.

## Satır 12-16: Başlık ve özet

```python
print("=" * 70)
print("CONFIGURATION")
print("=" * 70)
print(settings.describe())
print("=" * 70)
```

`"=" * 70` yetmiş tane eşittir işareti üretiyor. Python'da string ile sayı
çarpımı tekrarlama anlamına geliyor.

Dikkat: bu satırlar fonksiyon içinde değil, doğrudan modül seviyesinde. Küçük
betiklerde kabul edilebilir. Büyük dosyalarda `main()` fonksiyonu ve
`if __name__ == "__main__"` koruması tercih edilir, ki diğer dosyalarda öyle
yapılmış.

## Satır 17-21: Sonraki adımlar

```python
print("\nValid. Nothing was contacted: this only checks the values.")
print("Next: confirm the services are actually up.")
print(f"  curl {settings.llm_base_url}/models")
if settings.qdrant_url:
    print(f"  curl {settings.qdrant_url}/collections")
```

"Nothing was contacted" cümlesi bilinçli. Kullanıcı "geçerli" yazısını görüp
her şeyin hazır olduğunu sanabilir, oysa Ollama kapalı olabilir. Bu dosya
sadece **değerlerin** geçerli olduğunu söylüyor.

Sonrasında çalıştırılacak `curl` komutları, kullanıcının kendi ayarlarıyla
doldurulmuş halde basılıyor. Kopyala yapıştır ile test edebiliyor.

Satır 20'deki `if` kontrolü: Qdrant yerel dosya modundaysa `qdrant_url` boş
olur ve o zaman `curl` komutu anlamsız olurdu.

---

# hippo_factory.py

Ayarları HippoRAG nesnesine çeviren tek yer.

## Satır 1-8: Docstring

Mimari kararı açıklıyor: `settings.py` "ne konfigüre edilmiş" sorusunu,
bu dosya "nasıl kuruyoruz" sorusunu cevaplıyor. Kütüphaneyi import eden tek
dosya bu, yani motoru değiştirmek istersen dokunacağın yer belli.

## Satır 10-16: Importlar ve logger

```python
from __future__ import annotations

import logging

from settings import settings

logger = logging.getLogger(__name__)
```

`logging.getLogger(__name__)` bu modüle özel bir logger üretiyor. `__name__`
değişkeni modülün adını tutuyor, yani `"hippo_factory"`.

Neden `print` değil de logger: log seviyesi ayarlanabiliyor, çıktıya zaman
damgası ve modül adı eklenebiliyor, ve üretimde dosyaya yönlendirilebiliyor.
`print` bunların hiçbirini yapamıyor.

Neden `__name__` kullanılıyor: her modülün kendi logger'ı olunca, çıktıda
hangi mesajın nereden geldiği görünüyor ve seviyeler modül bazında
ayarlanabiliyor.

## Satır 19-21: Config kurucu ve gecikmeli import

```python
def build_base_config():
    """Translate our settings into HippoRAG's BaseConfig."""
    from hipporag.utils.config_utils import BaseConfig
```

Import fonksiyonun **içinde**, dosyanın başında değil. Buna **lazy import**
deniyor ve burada bilinçli bir tercih.

Sebebi: HippoRAG ağır bir kütüphane, import edilmesi saniyeler sürüyor ve
torch gibi devasa bağımlılıkları yüklüyor. `setup_logging` veya `banner`
fonksiyonlarını kullanmak isteyen bir betik, HippoRAG'i beklemek zorunda
kalmasın diye import buraya taşınmış.

Yan faydası: HippoRAG kurulu değilse bile `check_config.py` çalışıyor.

## Satır 23-46: BaseConfig kurulumu

```python
    return BaseConfig(
        # models
        llm_name=settings.extraction_model,
        llm_base_url=settings.llm_base_url,
        ...
    )
```

Bizim `Settings` nesnemizi HippoRAG'in beklediği `BaseConfig` nesnesine
çeviriyor. Bu bir **adapter** deseni: iki farklı arayüzü birbirine bağlıyor.

Parametre adları (`llm_name`, `synonymy_edge_sim_threshold`,
`preprocess_chunk_max_token_size`) HippoRAG'in kendi kaynak kodundan alındı,
tahminle değil. Yanlış bir isim yazsaydın Python sessizce yok saymazdı,
`TypeError` verirdi, ama var olan başka bir parametreyi yanlış anlasaydın
sessizce yanlış davranış üretirdi.

**Satır 44-45** özellikle önemli:

```python
        seed=42,
        temperature=0,
```

İkisi de **tekrarlanabilirlik** için. `temperature=0` modeli mümkün olduğunca
belirlenimci yapıyor, `seed=42` rastgeleliği sabitliyor.

Neden ölçüm yapan bir projede şart: iki çalıştırma arasındaki farkın senin
değişikliğinden mi yoksa modelin rastgeleliğinden mi geldiğini bilmen gerek.
Bu iki satır olmadan `SYNONYMY_THRESHOLD` deneyleri anlamsız olurdu.

42 sayısının özel bir anlamı yok, bu alanda geleneksel bir seçim.

## Satır 49-56: build_hipporag ve docstring

```python
def build_hipporag():
    """
    Build HippoRAG with a split extraction and answer model.

    HippoRAG accepts extraction_llm and qa_llm separately, so the split is
    native rather than a workaround. When both names match we pass one object
    and nothing is loaded twice.
    """
```

Docstring önemli bir bilgi veriyor: model ayrımı HippoRAG'in kendi desteklediği
bir şey, bizim uydurduğumuz bir numara değil. Bunu kütüphanenin kurucu
imzasını okuyarak doğruladım.

## Satır 57-64: Tek model durumu

```python
    from hipporag import HippoRAG

    config = build_base_config()

    if settings.extraction_model == settings.generation_model:
        logger.info("Using one model for extraction and generation: %s",
                    settings.extraction_model)
        return HippoRAG(global_config=config)
```

İki model adı aynıysa tek nesne kuruluyor ve erken dönülüyor.

Satır 62'deki `logger.info("... %s", değer)` yazımına dikkat: f-string
kullanılmamış. Sebebi performans: eğer log seviyesi INFO'nun üstündeyse
(mesela WARNING), logging kütüphanesi mesajı hiç biçimlendirmiyor. f-string
kullansaydın biçimlendirme her durumda yapılırdı.

Küçük bir kazanç ama logging kütüphanesinin standart kullanımı bu.

`return` ile erken çıkış, `else` bloğu yazmaktan daha okunaklı. Buna
**guard clause** deniyor.

## Satır 66-74: İki model durumu

```python
    from hipporag.llm import _get_llm_class

    qa_config = build_base_config()
    qa_config.llm_name = settings.generation_model
    qa_llm = _get_llm_class(qa_config)

    logger.info("Extraction: %s, generation: %s",
                settings.extraction_model, settings.generation_model)
    return HippoRAG(global_config=config, qa_llm=qa_llm)
```

**66:** Yine gecikmeli import. Ayrıca alt çizgiyle başlayan bir fonksiyon
kullanıyoruz (`_get_llm_class`), yani HippoRAG'in özel API'si. Bu bir risk:
kütüphane sürümü değişirse bu fonksiyon kaybolabilir. Alternatifi yoktu.

**68:** İkinci bir config nesnesi kuruluyor, çünkü `llm_name` alanını
değiştireceğiz ve birincisini bozmak istemiyoruz.

**69:** Sadece model adı değiştiriliyor, geri kalan ayarlar aynı.

**70:** O config'e uygun LLM sınıfı üretiliyor.

**74:** İki nesne birlikte veriliyor. `global_config` extraction için,
`qa_llm` cevap üretimi için.

## Satır 77-83: Logging kurulumu

```python
def setup_logging() -> None:
    """Apply LOG_LEVEL from the environment. Called by every entry point."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
```

`getattr(logging, "INFO", logging.INFO)` ifadesi `logging.INFO` sabitini
adından yola çıkarak buluyor. Üçüncü parametre varsayılan: `.env` dosyasına
`LOG_LEVEL=SACMA` yazılırsa çökmüyor, INFO'ya düşüyor.

Format dizesindeki `%(levelname)-7s` ifadesi seviye adını yedi karaktere
soldan hizalıyor. Böylece "INFO" ve "WARNING" satırlarında mesajlar aynı
sütunda başlıyor ve çıktı okunaklı oluyor.

`datefmt="%H:%M:%S"` tarihi atıp sadece saat gösteriyor. Bir oturumda tarih
zaten belli, yer kaplaması gereksiz.

## Satır 86-92: Banner

```python
def banner(title: str) -> None:
    """Print the resolved configuration at the start of a run."""
    print("=" * 70)
    print(title)
    print("-" * 70)
    print(settings.describe())
    print("=" * 70)
```

Her çalıştırmanın başında konfigürasyonu basıyor.

Neden değerli: iki hafta sonra "bu sonuç neden böyle çıkmış" diye
sorduğunda, log dosyasının başında hangi model ve hangi eşikle çalıştığı
yazılı oluyor. Ölçüm yapan bir projede bu bilgi sonucun kendisi kadar önemli.

---

# index.py

İlk gerçek iş yapan dosya. Korpusu indeksliyor ve ölçüyor.

## Satır 1-9: Docstring

```python
"""
Index a corpus and measure what it produces.

The reference figure is 120 edges per passage, measured by the HippoRAG 2
authors on MuSiQue. ...
"""
```

Referans sayıyı en başa koymak bilinçli: bu dosyayı açan kişi neye
bakacağını hemen bilsin.

## Satır 11-16: Importlar

```python
import json
import time
from pathlib import Path

from hippo_factory import banner, build_hipporag, setup_logging
from settings import settings
```

`json` metrikleri dosyaya yazmak için. `time` süre ölçmek için. `Path` dosya
yolları için.

`Path` neden `os.path` yerine: nesne yönelimli, işletim sistemi farklarını
kendisi hallediyor, ve `path.exists()` gibi metodlar `os.path.exists(path)`
yazmaktan okunaklı.

Son iki satır kendi modüllerimiz. Import sırası kuralına uygun: standart
kütüphane, boş satır, yerel modüller.

## Satır 19-23: read_docs ve docstring

```python
def read_docs(folder: str) -> list[str]:
    """
    Read .txt and .md files. HippoRAG chunks internally, so whole documents
    go in rather than pre split pieces.
    """
```

Docstring kritik bir uyarı içeriyor: dokümanları biz bölmüyoruz. HippoRAG
`preprocess_chunk_max_token_size` ayarıyla kendisi bölüyor. Biz de bölseydik
iki kez bölünmüş olurdu ve chunk boyutu ayarı anlamsızlaşırdı.

## Satır 24-29: Klasör kontrolü

```python
    path = Path(folder)
    if not path.exists():
        raise SystemExit(
            f"DOCS_FOLDER points at '{folder}', which does not exist. "
            f"Create it or change DOCS_FOLDER in .env."
        )
```

`raise SystemExit(mesaj)` programı hata mesajıyla sonlandırıyor. Traceback
göstermiyor, çünkü bu bir kod hatası değil, kullanıcı hatası.

Mesajın yapısı iyi bir örnek: **ne yanlış** (klasör yok), **hangi ayardan
geliyor** (DOCS_FOLDER), **ne yapılmalı** (oluştur veya ayarı değiştir).
Üçü birden olmadan iyi bir hata mesajı olmuyor.

## Satır 31-36: Dosyaları oku

```python
    docs = [
        text
        for f in sorted(path.rglob("*"))
        if f.is_file() and f.suffix.lower() in {".txt", ".md"}
        if (text := f.read_text(encoding="utf-8", errors="ignore").strip())
    ]
```

Bu bir **list comprehension** ve içinde birkaç ilginç şey var.

`path.rglob("*")` klasörü ve alt klasörlerini özyinelemeli tarıyor. `glob`
sadece o klasöre bakardı, `rglob`'daki r "recursive" demek.

`sorted(...)` sonucu alfabetik sıraya koyuyor. Neden önemli: işletim sistemi
dosyaları rastgele sırada verebilir. Sıralama, aynı korpusla iki kez
çalıştırdığında aynı sonucu almanı sağlıyor. Ölçüm yapan bir projede şart.

`f.suffix.lower() in {".txt", ".md"}` uzantı kontrolü. `.lower()` sayesinde
`.TXT` de yakalanıyor.

`errors="ignore"` bozuk karakterleri sessizce atlıyor. Tartışmalı bir tercih:
bozuk bir dosyayı fark etmeden indeksleyebilirsin. Ama alternatif olan çökmek,
tek bir bozuk dosya yüzünden tüm işi durdurur.

`if (text := ...)` ifadesindeki `:=` **walrus operatörü**, Python 3.8 ile
geldi. Hem atama yapıyor hem de değeri kontrol ediyor. Bu olmadan
`f.read_text()` çağrısını iki kez yazman gerekirdi: bir kez kontrol için, bir
kez listeye eklemek için. Dosya okuma pahalı bir işlem olduğu için bu fark
ediyor.

İki `if` art arda yazılabiliyor, aralarında `and` gerekmiyor. Comprehension
sözdiziminin bir özelliği.

## Satır 38-40: Boş sonuç kontrolü

```python
    if not docs:
        raise SystemExit(f"No .txt or .md files found under '{folder}'.")
    return docs
```

Klasör var ama içi boşsa da hata veriyor. Satır 25'teki kontrolden farklı bir
durum ve ayrı bir mesajı hak ediyor.

## Satır 43-45: main başlangıcı

```python
def main() -> None:
    setup_logging()
    banner("INDEXING")
```

Her giriş noktasının ilk iki satırı aynı: logging kur, konfigürasyonu bas.

## Satır 47-50: Girdi özeti

```python
    docs = read_docs(settings.docs_folder)
    total_chars = sum(len(d) for d in docs)
    print(f"documents      : {len(docs):,}")
    print(f"characters     : {total_chars:,}\n")
```

`sum(len(d) for d in docs)` bir **generator expression**. Köşeli parantez
olmadığı için tüm uzunlukları listeye toplamıyor, tek tek üretip topluyor.
Bellek açısından daha verimli.

`{len(docs):,}` biçimlendirmesindeki virgül binlik ayraç ekliyor: `12345`
yerine `12,345`. Büyük sayıları okunabilir yapıyor.

## Satır 52: HippoRAG'i kur

```python
    hipporag = build_hipporag()
```

Tek satır, ama arkasında modelin yüklenmesi ve Qdrant bağlantısının kurulması
var. Fabrika deseninin faydası burada görünüyor: bu dosya nasıl kurulduğunu
bilmek zorunda değil.

## Satır 54-56: İndeksle ve ölç

```python
    started = time.perf_counter()
    hipporag.index(docs=docs)
    elapsed = time.perf_counter() - started
```

`time.perf_counter()` en yüksek çözünürlüklü sayacı veriyor. `time.time()`
yerine bunun kullanılmasının sebebi: `time.time()` sistem saatine bağlı ve
saat ayarlanırsa (NTP senkronizasyonu gibi) ölçüm bozulur. `perf_counter`
monotonik, yani hiç geri gitmiyor.

Ölçtüğü şey **wall clock**, yani gerçek geçen süre. CPU süresi değil, ki
zaten burada beklenen çoğunlukla GPU ve ağ beklemesi.

## Satır 58-61: Grafı oku

```python
    # get_graph_info reads the embedding stores and the edge map, so these are
    # the counts that were actually written, not what we hoped for.
    info = hipporag.get_graph_info()
    passages = info["num_passage_nodes"]
```

Yorum önemli bir ayrımı vurguluyor: bu sayılar tahmin değil, gerçekten
yazılmış olan. Chunk sayısını kendimiz hesaplamaya çalışsaydık HippoRAG'in
chunking mantığını tahmin etmemiz gerekirdi.

`passages` değişkeni ayrı çekiliyor çünkü aşağıda bölen olarak birkaç kez
kullanılacak.

## Satır 63-78: Metrik sözlüğü

```python
    metrics = {
        "documents": len(docs),
        "characters": total_chars,
        "passages": passages,
        ...
        "synonymy_threshold": settings.synonymy_threshold,
        "vector_store": settings.vector_store_type,
    }
```

Ham sayılar. Son dört alan (`extraction_model`, `embedding_model`,
`synonymy_threshold`, `vector_store`) ölçümün değil, **koşulların** kaydı.

Neden gerekli: üç ay sonra bu dosyayı açtığında hangi ayarla ölçtüğünü
bilmen lazım. Ölçüm sonucu koşulsuz anlamsızdır.

`round(elapsed, 1)` süreyi bir ondalık haneye yuvarlıyor. JSON dosyasında
`1234.5678901` görmek gereksiz.

## Satır 80-88: Türetilmiş oranlar

```python
    if passages:
        metrics |= {
            "edges_per_passage": round(info["num_total_triples"] / passages, 1),
            "nodes_per_passage": round(info["num_total_nodes"] / passages, 1),
            "seconds_per_passage": round(elapsed / passages, 2),
            "synonymy_share": round(
                info["num_synonymy_triples"] / max(1, info["num_total_triples"]), 3
            ),
        }
```

`if passages` kontrolü sıfıra bölmeyi engelliyor. İndeksleme başarısız
olduysa passage sayısı sıfır olabilir.

`metrics |= {...}` sözlük birleştirme operatörü, Python 3.9 ile geldi.
`metrics.update({...})` ile aynı iş.

`max(1, ...)` ifadesi ayrı bir sıfıra bölme koruması: passage var ama hiç
kenar yoksa (extraction tamamen başarısızsa) bölen sıfır olurdu.

Bu dört oran projenin asıl ürünü:

- **edges_per_passage**: makalenin 120 rakamıyla karşılaştırılacak
- **nodes_per_passage**: graf yapısının ikinci göstergesi
- **seconds_per_passage**: tam korpusun ne kadar süreceğini verir
- **synonymy_share**: makalede yaklaşık %80, sapma varsa eşik ayarı gerekir

`synonymy_share` üç ondalığa yuvarlanmış (0.803 gibi) çünkü yüzdeye
çevrildiğinde tek ondalık hassasiyet kalıyor.

## Satır 90: Dosyaya yaz

```python
    Path(settings.metrics_file).write_text(json.dumps(metrics, indent=2))
```

`json.dumps(metrics, indent=2)` sözlüğü girintili JSON metnine çeviriyor.
`indent=2` olmadan tek satırlık okunmaz bir çıktı olurdu.

`Path.write_text` dosyayı açıp yazıp kapatıyor, tek satırda. `open()` ve
`with` bloğu yazmaya gerek kalmıyor.

Neden JSON: `stats.py` bu dosyayı okuyacak, yani makine tarafından
işlenebilir olması gerekiyor. Aynı zamanda insan da okuyabiliyor.

## Satır 92-107: Özet çıktı

```python
    print("\n" + "=" * 70)
    print(f"indexed in {elapsed / 60:.1f} min")
    ...
```

`elapsed / 60` saniyeyi dakikaya çeviriyor. `:.1f` bir ondalık hane.

Satır 96-98 tek bir `print` çağrısı, üç f-string yan yana. Çıktıda tek satır
oluyor ama kodda üç satıra bölünmüş.

Satır 100-104 karşılaştırmalı çıktı: senin sayının yanında makalenin sayısı.
Tek başına "142 kenar" bir şey söylemiyor, "142, makale 120" bir şey söylüyor.

`{metrics['synonymy_share']:.0%}` biçimlendirmesi 0.803 değerini `%80` olarak
yazıyor. Yüzde işareti otomatik ekleniyor ve 100 ile çarpılıyor.

Satır 106 sonraki adımı söylüyor. Küçük ama faydalı: kullanıcı ne yapacağını
düşünmek zorunda kalmıyor.

## Satır 110-111: Giriş noktası koruması

```python
if __name__ == "__main__":
    main()
```

Python'da her modülün `__name__` değişkeni var. Doğrudan çalıştırıldığında
`"__main__"` oluyor, import edildiğinde modülün adı oluyor.

Bu koruma sayesinde `import index` yazan biri `main()` fonksiyonunun
çalışmasını tetiklemiyor. Test yazarken veya fonksiyonları başka yerden
kullanırken gerekli.

`check_config.py` bu korumayı kullanmıyor, çünkü orada dosyanın tamamı zaten
yan etkiden ibaret. Bu bir tutarsızlık ve daha büyük bir projede
düzeltilmesi gerekirdi.

---

# stats.py

Ölçümü kapasite planına çeviriyor. Kendisi hiçbir şey ölçmüyor.

## Satır 7-10: Importlar

```python
import json
from pathlib import Path

from settings import settings
```

HippoRAG import edilmiyor. Bu dosya sadece JSON okuyup aritmetik yapıyor,
yani modele veya veritabanına ihtiyacı yok. Saniyeler içinde çalışıyor.

## Satır 12-13: Referans sabitler

```python
PAPER_EDGES_PER_PASSAGE = 120
PAPER_MB_PER_PASSAGE = 0.85  # 9.9 GB over 11,656 passages, parquet backend
```

Büyük harfle yazılması sabit olduklarını belirten Python konvansiyonu.
Zorlayıcı değil, sadece konvansiyon.

Yorumdaki hesap denetlenebilirliği sağlıyor: 9.9 GB ÷ 11.656 passage ≈ 0.85
MB. Sayıyı nereden aldığımı bilmeyen biri kontrol edebilir.

Modül seviyesinde tanımlanmaları bilinçli: fonksiyonun içine gömseydin,
değiştirmek isteyen kişi aramak zorunda kalırdı.

## Satır 16-21: Bayt biçimlendirici

```python
def human(mb: float) -> str:
    if mb < 1024:
        return f"{mb:.0f} MB"
    if mb < 1024 * 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb / 1024 / 1024:.1f} TB"
```

Megabaytı okunabilir birime çeviriyor. `85000 MB` yerine `83.0 GB`.

`else` kullanılmamış, çünkü her `if` bloğu `return` ile bitiyor. Bu **early
return** deseni ve girinti seviyesini düşük tutuyor.

`:.0f` MB için ondalık göstermiyor, `:.1f` GB ve TB için bir hane gösteriyor.
Sebep: 512 MB'ta ondalık gereksiz, 1.5 TB'ta anlamlı.

## Satır 24-32: Dosyayı oku ve doğrula

```python
def main() -> None:
    path = Path(settings.metrics_file)
    if not path.exists():
        raise SystemExit(f"No {settings.metrics_file}. Run index.py first.")

    m = json.loads(path.read_text())
    passages = m.get("passages") or 0
    if not passages:
        raise SystemExit("No passages recorded. Did indexing finish?")
```

İki ayrı hata durumu: dosya yok, veya dosya var ama içi anlamsız. İkincisi
indeksleme yarıda kesilirse oluşabilir.

`m.get("passages") or 0` iki koruma birden: anahtar yoksa `get` `None`
döndürüyor, `or 0` onu sıfıra çeviriyor. `m["passages"]` yazsaydık `KeyError`
alırdık.

Değişken adının `m` olması kısa ama bu fonksiyonda çok sık kullanıldığı için
kabul edilebilir. Daha uzun bir fonksiyonda `metrics` yazmak gerekirdi.

## Satır 34-35: Kısa isimler

```python
    epp = m["edges_per_passage"]
    spp = m["seconds_per_passage"]
```

Aşağıda defalarca kullanılacakları için kısaltılmış. `edges per passage` ve
`seconds per passage` baş harfleri.

## Satır 37-50: Ölçüm çıktısı

```python
    print(f"documents           {m['documents']:,}")
    print(f"passages            {passages:,}")
    ...
```

Alan adlarından sonraki boşluklar sayıları aynı sütuna hizalıyor. Elle
sayılmış boşluklar, kırılgan ama küçük bir dosyada kabul edilebilir.

Satır 45-46 iki satıra bölünmüş tek bir print: eşanlamlı sayısı ve yüzdesi
birlikte gösteriliyor.

## Satır 52-64: Yoğunluk yorumu

```python
    ratio = epp / PAPER_EDGES_PER_PASSAGE
    print("\n" + "-" * 70)
    if ratio > 1.3:
        print(f"Your corpus is {ratio:.1f}x denser than the paper's.")
        print("Technical text reuses terminology, which multiplies synonym")
        print("edges. Raise SYNONYMY_THRESHOLD to 0.85 and measure again.")
    elif ratio < 0.7:
        ...
```

Sayıyı yorumlayan kısım. Ham sayı bir şey söylemiyor, "makaleden 1.8 kat
yoğun, bunun sebebi muhtemelen şu, şunu deneyin" bir şey söylüyor.

1.3 ve 0.7 eşikleri keyfi ama makul: %30 sapma gürültü sayılmaz.

Düşük yoğunluk için verilen uyarı ilginç: küçük graf iyi haber gibi görünür,
ama extraction hiç varlık bulamadıysa da küçük olur. Kullanıcıyı yanlış
sevinmekten koruyor.

## Satır 66-75: Projeksiyon tablosu

```python
    print(f"{'passages':>12}  {'edges':>14}  {'RAM if parquet':>15}  {'index':>10}")
    print("-" * 70)
    for target in (10_000, 100_000, 1_000_000, 10_000_000):
        hours = spp * target / 3600
        t = f"{hours:.1f} h" if hours < 48 else f"{hours / 24:.0f} d"
        print(f"{target:>12,}  {int(epp * target):>14,}  "
              f"{human(PAPER_MB_PER_PASSAGE * target):>15}  {t:>10}")
```

`{'passages':>12}` ifadesindeki `>12` sağa hizalayıp on iki karaktere
tamamlıyor. Sayı kolonlarında sağa hizalama standart, çünkü basamaklar
alt alta geliyor.

`10_000` yazımındaki alt çizgiler Python'da basamak ayracı, okunabilirlik
için. Değeri etkilemiyor.

Satır 73 bir **koşullu ifade** (ternary): 48 saatten azsa saat cinsinden, çok
ise gün cinsinden gösteriyor. `1247.3 h` okunmaz, `52 d` okunur.

`int(epp * target)` ondalığı atıyor, çünkü kenar sayısı tam sayı olmalı.

## Satır 77-84: Backend'e göre mesaj

```python
    if settings.vector_store_type == "qdrant":
        print("\nThe RAM column is what the parquet backend would have needed.")
        ...
    else:
        print(f"\nVECTOR_STORE_TYPE={settings.vector_store_type}: the RAM column")
        print("applies to you directly. Switch to qdrant before it bites.")
```

Aynı tablo iki farklı anlam taşıyor ve hangisinin geçerli olduğu ayara bağlı.

Qdrant kullanıyorsan RAM kolonu bir uyarı değil, kaçındığın maliyetin
gösterimi. Parquet kullanıyorsan doğrudan senin faturan.

Bu ayrımı yapmasaydık kullanıcı 850 GB rakamını görüp gereksiz yere panikleyebilirdi.

---

# query.py

Soru sorar, gecikme ölçer.

## Satır 1-14: Docstring

```python
"""
Ask questions against the indexed graph, and measure latency.

Two modes, and the difference is a debugging tool:
  qa        full pipeline, writes an answer
  retrieve  passages only, which isolates retrieval from the answer model

When an answer is wrong, run retrieve first. If the right passage never came
back, changing the answer model will not help.
"""
```

Docstring bir kullanım talimatı değil, bir **teşhis stratejisi** anlatıyor.
İki modun neden var olduğu ve hangi sırayla kullanılacağı yazılı.

## Satır 16-23: Importlar ve sabit

```python
import argparse
import statistics
import time
from pathlib import Path

from hippo_factory import banner, build_hipporag, setup_logging

QUESTIONS_FILE = "questions.txt"
```

`argparse` komut satırı argümanlarını ayrıştırıyor.

`statistics` standart kütüphanede ve medyan hesabı için kullanılıyor. `numpy`
kurmaya gerek yok.

`settings` import edilmemiş, çünkü bu dosya doğrudan ayarlara erişmiyor.
`build_hipporag` içinde kullanılıyor ama o başka dosyanın işi.

`QUESTIONS_FILE` modül seviyesinde sabit. Ayara taşınabilirdi ama nadiren
değişecek bir şey.

## Satır 26-34: Soruları yükle

```python
def load_questions() -> list[str]:
    path = Path(QUESTIONS_FILE)
    if not path.exists():
        raise SystemExit(
            f"No {QUESTIONS_FILE}. Write 20 to 30 real questions there, "
            f"one per line. A question set from the people who will use the "
            f"system is worth more than any published benchmark."
        )
    return [q.strip() for q in path.read_text().splitlines() if q.strip()]
```

Hata mesajı sadece "dosya yok" demiyor, **ne yazılması gerektiğini** ve
**neden önemli olduğunu** da söylüyor. Bu proje için gerçek bir tavsiye:
kullanıcılardan gelen sorular, herhangi bir benchmark'tan değerli.

Son satırdaki comprehension iki iş yapıyor: her satırı kırpıyor ve boş
satırları atıyor. Böylece `questions.txt` dosyasında boş satır bırakabiliyorsun.

`.splitlines()` satır sonu karakterlerinin farklı işletim sistemlerindeki
biçimlerini (`\n`, `\r\n`) hallediyor. `.split("\n")` Windows dosyalarında
sonda `\r` bırakırdı.

## Satır 37-43: Argüman ayrıştırma

```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="*", help="ask a single question")
    parser.add_argument("--retrieve", action="store_true",
                        help="show retrieved passages instead of answers")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
```

`nargs="*"` sıfır veya daha fazla değer kabul ediyor. Yani `python query.py`
de, `python query.py "soru"` da geçerli.

`action="store_true"` bayrak davranışı: `--retrieve` yazılırsa `True`,
yazılmazsa `False`. Değer beklemiyor.

`--top-k` yazımı Python'da `args.top_k` olarak erişiliyor. argparse tireyi
alt çizgiye çeviriyor.

`argparse` otomatik olarak `--help` desteği ekliyor, ayrıca bilinmeyen bir
argüman verilirse anlamlı hata mesajı üretiyor.

## Satır 45-49: Kurulum

```python
    setup_logging()
    banner("RETRIEVAL" if args.retrieve else "QUESTION ANSWERING")

    questions = args.question or load_questions()
    hipporag = build_hipporag()
```

Satır 46'daki koşullu ifade banner başlığını moda göre değiştiriyor.

Satır 48'deki `or` kalıbı: komut satırında soru verildiyse onu kullan,
verilmediyse dosyadan oku. Boş liste `False` sayıldığı için çalışıyor.

## Satır 51-53: Döngü başlangıcı

```python
    latencies: list[float] = []
    for question in questions:
        started = time.perf_counter()
```

Her sorunun süresi ayrı ayrı ölçülüyor, çünkü sonunda medyan ve p95
hesaplanacak.

## Satır 55-61: Retrieve modu

```python
        if args.retrieve:
            solutions = hipporag.retrieve(queries=[question],
                                          num_to_retrieve=args.top_k)
            took = time.perf_counter() - started
            print(f"\nQ: {question}")
            for i, doc in enumerate(solutions[0].docs[: args.top_k], 1):
                print(f"  {i}. {doc.replace(chr(10), ' ')[:180]}...")
```

`queries=[question]` tek soruyu bile listeye sarıyor, çünkü HippoRAG'in API'si
toplu işlem için tasarlanmış.

`solutions[0]` ilk (ve tek) sonucu alıyor.

`enumerate(..., 1)` numaralandırmayı 1'den başlatıyor. Varsayılan 0'dır ama
kullanıcıya gösterilen listede 1'den başlamak doğal.

`doc.replace(chr(10), ' ')` satır sonlarını boşluğa çeviriyor, böylece her
passage tek satırda görünüyor. `chr(10)` yeni satır karakteri; f-string
içinde ters eğik çizgi kullanılamadığı için bu yöntemle yazılmış (Python 3.12
öncesinde bir kısıt).

`[:180]` ilk 180 karakteri alıyor. Passage'ın tamamını basmak ekranı doldururdu.

## Satır 62-66: QA modu

```python
        else:
            solutions, _, _ = hipporag.rag_qa(queries=[question])
            took = time.perf_counter() - started
            print(f"\nQ: {question}")
            print(f"A: {solutions[0].answer}")
```

`rag_qa` üç değer döndürüyor ama sadece ilki lazım. `_` konvansiyonu
"bu değeri kullanmayacağım" demek. Python'da özel bir anlamı yok, sadece
okuyucuya niyet bildiriyor.

Süre ölçümü her iki dalda ayrı ayrı yapılıyor (satır 58 ve 64), çünkü çıktı
basılmadan önce ölçülmeli. Basma işlemi de zaman alır ve ölçüme karışmamalı.

## Satır 68-69: Kaydet ve göster

```python
        latencies.append(took)
        print(f"   [{took:.1f}s]")
```

Süre hem listeye ekleniyor hem de o an gösteriliyor. Anlık geri bildirim
uzun çalışmalarda önemli.

## Satır 71-78: İstatistik

```python
    if len(latencies) > 1:
        ordered = sorted(latencies)
        p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
        print("\n" + "=" * 70)
        print(f"questions {len(latencies)}   "
              f"median {statistics.median(latencies):.1f}s   p95 {p95:.1f}s")
        print("Reference: the paper measures 1.2s per query with a served 70B.")
```

`if len(latencies) > 1` tek soru sorulduysa istatistik basmıyor. Tek ölçümün
medyanı kendisidir, göstermek gereksiz.

p95 hesabı: listeyi sırala, %95'inci sıradaki elemanı al. `max(0, ...)`
negatif indeksi engelliyor (çok az eleman varsa gerekli), `-1` ise listelerin
sıfırdan başlamasını telafi ediyor.

Bu basit bir p95 tanımı, istatistiksel olarak interpolasyonlu versiyonları da
var. Bu ölçekte fark etmiyor.

Neden p95: ortalama, birkaç yavaş sorguyu gizler. Kullanıcı deneyimini
belirleyen kötü durumdur, ortalama değil.

Son satır yine karşılaştırma sağlıyor: senin sayının yanında referans.

---

# test_identifiers.py

Model kodu ve hata kodu aramasını test ediyor. Bu projeye özel, hiçbir
benchmark'ta olmayan bir test.

## Satır 1-10: Docstring

```python
"""
Check whether exact identifiers survive indexing and retrieval.

Dense embeddings are weak on literal strings: a query for ERR-42 can rank
ERR-24 just as highly. Worse, if extraction never made the code a phrase node,
the graph cannot help at all. No published benchmark tests this, because none
of their corpora contains part numbers.
"""
```

Testin var olma sebebini anlatıyor. Bu bilgi olmadan biri dosyayı gereksiz
sanıp silebilir.

## Satır 17-22: Kurulum

```python
def main(tokens: list[str]) -> None:
    setup_logging()
    banner("IDENTIFIER TEST")

    hipporag = build_hipporag()
    phrases = list(hipporag.entity_embedding_store.get_all_texts())
```

`entity_embedding_store` grafın varlık düğümlerini tutan depo.
`get_all_texts()` hepsinin metnini veriyor.

`list(...)` sarması sonucu belleğe alıyor, çünkü aşağıda döngü içinde
defalarca taranacak. Generator olsaydı ilk taramadan sonra tükenirdi.

## Satır 24-27: Döngü ve normalize

```python
    for token in tokens:
        low = token.lower()
        print("=" * 70)
        print(f"identifier: {token}")
```

`low` değişkeni karşılaştırmalar için küçük harfe çevrilmiş hali. Bir kez
hesaplanıp defalarca kullanılıyor.

## Satır 29-30: İki tür eşleşme

```python
        exact = [p for p in phrases if low == p.lower()]
        partial = [p for p in phrases if low in p.lower() and low != p.lower()]
```

**Tam eşleşme**: kod tek başına bir varlık olmuş. En iyi durum.

**Kısmi eşleşme**: kod daha uzun bir ifadenin içinde geçiyor, mesela
"Model X200 filter assembly". Bu durumda arama daha zor ama imkânsız değil.

`partial` tanımındaki `and low != p.lower()` koşulu tam eşleşmeleri kısmi
listesinden çıkarıyor, yoksa aynı şey iki listede birden olurdu.

## Satır 32-41: Sonucu yorumla

```python
        if exact:
            print(f"  exact phrase node : {exact[0]}")
        elif partial:
            print(f"  folded into       : {', '.join(partial[:5])}")
            print("  -> extraction merged it into a longer phrase.")
        else:
            print("  NOT a phrase node.")
            print("  -> extraction dropped it. Dense retrieval will not find")
            print("     it reliably. This is the case for a lexical index over")
            print("     the raw text, in PostgreSQL or Qdrant sparse vectors.")
```

Üç durumun her biri farklı bir eylem gerektiriyor:

Tam eşleşme varsa sorun yok.

Kısmi eşleşme varsa extraction kodu daha uzun bir ifadeye gömmüş. Prompt
veya şema ayarıyla düzeltilebilir.

Hiç yoksa extraction kodu tamamen atmış. Bu durumda hiçbir retrieval ayarı
işe yaramaz, lexical bir indeks eklemen gerekiyor. Mesajda çözüm de yazılı.

`partial[:5]` en fazla beş örnek gösteriyor, yüzlerce eşleşme olabilir.

## Satır 43-50: Retrieval testi

```python
        solutions = hipporag.retrieve(
            queries=[f"What information is available about {token}?"],
            num_to_retrieve=3,
        )
        print("\n  top passages:")
        for i, doc in enumerate(solutions[0].docs[:3], 1):
            hit = "HIT " if low in doc.lower() else "MISS"
            print(f"    {i}. [{hit}] {doc.replace(chr(10), ' ')[:150]}...")
```

Grafta olması yetmiyor, doğru passage'ın gelmesi de gerekiyor. Bu ikinci
aşama.

`hit` değişkeni dönen passage'da kodun geçip geçmediğine bakıyor. Basit ama
etkili bir kontrol: passage o koddan bahsetmiyorsa yanlış sonuç gelmiş
demektir.

`"HIT "` sonundaki boşluk `"MISS"` ile aynı genişlikte olsun diye. Çıktıda
köşeli parantezler hizalı duruyor.

## Satır 52-54: Yorum

```python
        print(f"\n  A MISS at rank 1 means the system answered about something")
        print(f"  other than {token}. On a manual corpus that is the failure")
        print("  that matters most, and aggregate scores hide it.")
```

Sonucun nasıl okunacağını söylüyor. Son cümle önemli: toplu skorlar bu hatayı
gizliyor, çünkü yüz sorudan üçünde yanlış kod getirmek ortalamayı çok az
düşürüyor ama kullanıcı için felaket.

## Satır 58-61: Giriş noktası

```python
if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python test_identifiers.py X200 ERR-42 ...")
    main(sys.argv[1:])
```

`sys.argv[0]` betiğin adı, `[1:]` gerisi. En az bir argüman şart.

`argparse` kullanılmamış çünkü ihtiyaç basit: sadece bir liste alınıyor,
bayrak yok.

---

# test_revision.py

Ekleme ve silme döngüsünü test ediyor.

## Satır 1-10: Docstring

```python
"""
Test the revision cycle: add a manual, then remove it.

A superseded procedure that stays in the index is a safety problem for device
documentation, not an inconvenience. HippoRAG's delete() uses reference
counting, so a triple only goes if no remaining document produced it. This
verifies that on your data instead of trusting the description.
"""
```

İki bilgi: neden önemli (güvenlik meselesi) ve nasıl çalışıyor (referans
sayımı). İkincisi sonucun yorumlanması için gerekli.

## Satır 19-25: Anlık görüntü

```python
def snapshot(hipporag) -> dict:
    info = hipporag.get_graph_info()
    return {
        "passages": info["num_passage_nodes"],
        "phrases": info["num_phrase_nodes"],
        "edges": info["num_total_triples"],
    }
```

`get_graph_info()` yedi alan döndürüyor ama biz üçünü alıyoruz. Karşılaştırma
için bu üçü yeterli ve çıktı okunaklı kalıyor.

Sözlük döndürmek karşılaştırmayı kolaylaştırıyor: satır 62'de `==` ile iki
sözlük doğrudan karşılaştırılabiliyor.

`hipporag` parametresine tip ipucu verilmemiş, çünkü tip HippoRAG'den geliyor
ve onu import etmek bu dosyada gecikmeli import mantığını bozardı.

## Satır 28-30: Biçimli çıktı

```python
def show(label: str, s: dict) -> None:
    print(f"{label:<20} passages {s['passages']:>7,}   "
          f"phrases {s['phrases']:>7,}   edges {s['edges']:>9,}")
```

`{label:<20}` etiketi sola hizalayıp yirmi karaktere tamamlıyor. Sayılar
`>7` ve `>9` ile sağa hizalı. Sonuç: üç satır alt alta okunabilir bir tablo.

Ayrı bir fonksiyon olması tekrarı önlüyor, üç kez çağrılıyor.

## Satır 33-41: Hazırlık

```python
def main(doc_path: str) -> None:
    setup_logging()
    banner("REVISION TEST")

    text = Path(doc_path).read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        raise SystemExit(f"{doc_path} is empty.")

    hipporag = build_hipporag()
```

Dosya en başta okunuyor, çünkü hem eklemede hem silmede aynı metin
kullanılacak. HippoRAG dokümanları içeriklerinden türetilen hash ile
tanıdığı için, silerken de aynı metni vermek gerekiyor.

## Satır 43-51: Ekleme

```python
    before = snapshot(hipporag)
    show("before", before)

    print("\nadding...")
    t0 = time.perf_counter()
    hipporag.index(docs=[text])
    add_time = time.perf_counter() - t0
    show("after add", snapshot(hipporag))
    print(f"  {add_time:.1f}s")
```

`before` değişkende saklanıyor çünkü sonda karşılaştırılacak. `after add`
saklanmıyor, sadece gösteriliyor.

## Satır 53-59: Silme

```python
    print("\ndeleting the same document...")
    t0 = time.perf_counter()
    hipporag.delete(docs_to_delete=[text])
    del_time = time.perf_counter() - t0
    after_del = snapshot(hipporag)
    show("after delete", after_del)
```

`delete(docs_to_delete=[text])` çağrısı metnin kendisini alıyor, bir kimlik
değil. HippoRAG içeride hash'ini hesaplayıp eşleşen chunk'ları buluyor.

## Satır 61-72: Sonuç yorumu

```python
    if after_del == before:
        print("Clean: the graph returned to its exact starting state.")
    else:
        print("Not identical, which can still be correct.")
        for key in ("passages", "phrases", "edges"):
            diff = after_del[key] - before[key]
            if diff:
                print(f"  {key}: {diff:+,} left behind")
        print("\nLeftover phrases and edges are expected when another document")
        print("also produced them: reference counting keeps shared facts alive.")
        print("Leftover passages are not expected and indicate a real problem.")
```

İki sözlük `==` ile karşılaştırılıyor. Python sözlükleri anahtar ve değer
bazında karşılaştırıyor, sıra önemli değil.

`{diff:+,}` biçimlendirmesindeki `+` işareti pozitif sayılarda da işaret
gösteriyor: `5` yerine `+5`. Fark olduğu anlaşılıyor.

`if diff` sıfır farkları atlıyor, sadece değişen alanlar yazılıyor.

Son üç satır sonucu yorumluyor ve **kritik bir ayrım** yapıyor: artakalan
ifade ve kenar normal, artakalan passage anormal. Bu ayrım olmadan kullanıcı
her farkı hata sanardı.

## Satır 74-78: Maliyet notu

```python
    print(f"\nadd {add_time:.1f}s, delete {del_time:.1f}s at this corpus size.")
    print("Delete rebuilds the retrieval objects, so it grows with the corpus.")
    print("Measure it again on the full corpus: this number decides whether")
    print("revisions stay practical.")
```

"at this corpus size" ifadesi önemli bir uyarı: bu süreler korpus büyüdükçe
değişecek. Küçük bir örnekte hızlı olması gerçek korpusta da hızlı olacağı
anlamına gelmiyor.

Silme işlemi retrieval nesnelerini yeniden kuruyor, yani embedding'ler tekrar
yükleniyor. Bu maliyet korpusla doğru orantılı büyüyor.

## Satır 81-84: Giriş noktası

```python
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python test_revision.py path/to/manual.txt")
    main(sys.argv[1])
```

`!= 2` tam olarak bir argüman istiyor (betik adı + bir dosya yolu).
`test_identifiers.py`'daki `< 2` kontrolünden farklı, çünkü orada birden fazla
kod verilebiliyor.

---

# Sonuç: kodda tekrar eden desenler

Dosyalar arasında kasıtlı olarak tekrarlanan yedi kalıp var. Bunları bir kez
öğrenirsen kodun tamamı okunaklı hale geliyor.

**1. Docstring önce, kod sonra.** Her dosya ve her önemli fonksiyon neden var
olduğunu anlatan bir docstring ile başlıyor. "Ne yapıyor" koddan okunur,
"neden var" okunmaz.

**2. Erken çıkış.** Hata durumları `raise SystemExit` ile en başta ele
alınıyor, `if/else` yuvaları kurulmuyor. Girinti seviyesi düşük kalıyor.

**3. Hata mesajı üç parçalı.** Ne yanlış, nereden geliyor, ne yapılmalı.
Üçü de olmadan mesaj eksik.

**4. Ölçüm her zaman karşılaştırmalı.** Hiçbir sayı tek başına basılmıyor,
yanında referans değer var. "142" bir şey söylemiyor, "142, makale 120"
söylüyor.

**5. Gecikmeli import.** Ağır kütüphaneler fonksiyon içinde import ediliyor,
böylece onlara ihtiyacı olmayan betikler hızlı başlıyor.

**6. Tekrarlanabilirlik sabitleri.** `seed=42`, `temperature=0`, `sorted(...)`.
Üçü de aynı amaca hizmet ediyor: aynı girdi aynı çıktıyı versin.

**7. Yorum, sonucun kendisi kadar önemli.** Her ölçüm çıktısı sonunda ne
anlama geldiğini ve ne yapılması gerektiğini yazıyor. Sayıyı üretmek kolay,
yorumlamak zor.
