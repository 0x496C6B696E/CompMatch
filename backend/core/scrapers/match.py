"""
Ürün adı <-> mağaza başlığı / slug / benchmark adı eşleştirme.

Token'lar küçük harfe çevrilir, "Ryzen 7" -> "r7", "8 GB"/"8G" -> "8gb", "2 TB" -> "2tb" normalize edilir.

ZORUNLU token'lar (adayda bulunmazsa skor 0):
  * en az 3 rakam içerenler: 4060, 13620h, 7735hs, b760m, 155h
  * harf+rakam karışık olanlar: i5, r7, m3, ddr4, ds3h, f15, e14 ve kapasiteler (8gb, 2tb)
    - kapasiteler strict=True (benchmark) modunda zorunlu değil: PassMark adında bellek yazmaz
  * 4+ harfli seri kelimeleri: slim, vivobook, legion, thinkpad, nitro, fury...
  Rakam içeren token aday token'ının başında ve ardından rakam gelerek de sayılır ("13700h16gb1" ✓),
  ama "7600x" ≠ "7600", "4060ti" ≠ "4060".
AYRICA:
  * marka (ilk anlamlı token) adayda olmalı;
  * varyant kelimeleri (ti, super, xt, pro, max, plus, ultra, air...) iki tarafta aynı olmalı;
  * strict=True: adayın kendi 3+ rakamlı token'ları da bizde olmalı ("Intel UHD 630" ≠ "Intel UHD Graphics").
Tek/iki haneli çıplak sayılar ("5", "15", "16") belirsizdir, sayılmaz.
Skor = eşleşen anlamlı token / toplam anlamlı token (0..1). Kalan yumuşak token'lar: 1-3 harfli kelimeler (rx, xe, tuf).
"""
import re

STOP = {
    "nvidia", "geforce", "amd", "radeon", "intel", "core", "apple", "gaming", "laptop", "notebook",
    "notbuk", "noutbuk", "the", "and", "with", "gb", "tb", "ssd", "ram", "nvme", "wifi", "oc", "edition",
    "graphics", "gpu", "cpu", "processor", "prosessor", "videokart", "desktop", "pc", "mainboard", "motherboard",
}
VARIANTS = {"ti", "super", "xt", "xtx", "x3d", "pro", "max", "plus", "ultra", "mini", "air"}
# Bileşen ararken sistem (hazır PC / laptop) ilanlarını ele
SYSTEM_WORDS = {"notbuk", "notebook", "noutbuk", "laptop", "desktop", "tower", "monoblok", "allinone", "komputer", "kompüter", "pc"}

_split = re.compile(r"[^a-z0-9]+")
_cap = re.compile(r"^\d+(gb|tb)$")


def tokens(text):
    raw = [t for t in _split.split(text.lower()) if t]
    out, i = [], 0
    while i < len(raw):
        t, nxt = raw[i], raw[i + 1] if i + 1 < len(raw) else ""
        if t == "ryzen" and nxt.isdigit() and len(nxt) == 1:            # "ryzen 7" -> "r7"
            out.append(f"r{nxt}"); i += 2; continue
        if t.isdigit() and nxt in ("gb", "g", "tb", "t"):              # "8 gb" / "2 tb" -> "8gb" / "2tb"
            out.append(f"{t}{nxt[0]}b"); i += 2; continue
        m = re.fullmatch(r"(\d+)([gt])", t)                             # "8g" -> "8gb"
        out.append(f"{m.group(1)}{m.group(2)}b" if m else t)
        i += 1
    return out


def flat(text):
    return "".join(tokens(text))


def _digits(t):
    return sum(c.isdigit() for c in t)


def required(toks, capacity=True):
    """Zorunlu token'lar; bkz. modül açıklaması."""
    out = []
    for t in toks:
        if t in VARIANTS:
            continue
        mixed = any(c.isdigit() for c in t) and any(c.isalpha() for c in t)
        if _digits(t) >= 3 or (mixed and (capacity or not _cap.match(t))) or (t.isalpha() and len(t) >= 4):
            out.append(t)
    return out


def _meaningful(name):
    return [t for t in tokens(name) if t not in STOP and not (t.isdigit() and len(t) < 3)]


def _present(tok, cand, haystack):
    if tok.isalpha():
        return tok in cand or tok in haystack
    pat = re.compile(rf"^{re.escape(tok)}(?:\d|$)")
    return any(pat.match(c) for c in cand)


def similarity(name, text, strict=False):
    """0.0: zorunlu/marka/varyant kuralı bozuldu; aksi halde anlamlı token'ların eşleşme oranı."""
    toks = _meaningful(name)
    if not toks:
        return 0.0
    cand = tokens(text)
    cand_set, haystack = set(cand), "".join(cand)
    if any(not _present(r, cand_set, haystack) for r in required(toks, capacity=not strict)):
        return 0.0
    if strict and any(_digits(r) >= 3 and r not in flat(name) for r in required(cand)):
        return 0.0
    name_set = set(toks)
    if any((v in cand_set) != (v in name_set) for v in VARIANTS):
        return 0.0
    hits = sum(1 for t in toks if t in cand_set or (len(t) >= 4 and t in haystack))
    return hits / len(toks)


def is_system(text):
    """Başlık hazır PC / laptop ilanı mı? (bileşen fiyatı olarak alınmamalı)"""
    return any(w in SYSTEM_WORDS for w in tokens(text))


def best(name, candidates, key=lambda c: c, threshold=0.6, strict=False):
    """En benzer adayı (aday, skor) olarak döndürür; eşitlikte kısa metin kazanır. Yoksa (None, 0)."""
    scored = [(c, similarity(name, key(c), strict)) for c in candidates]
    scored = [(c, s) for c, s in scored if s >= threshold]
    if not scored:
        return None, 0.0
    scored.sort(key=lambda cs: (-cs[1], len(key(cs[0]))))
    return scored[0]


def query_for(name):
    """Mağaza aramasına gidecek kısa sorgu: parantez içi atılır, gürültü kelimeler çıkar."""
    base = re.sub(r"\(.*?\)", " ", name)
    return " ".join(t for t in tokens(base) if t not in STOP)[:60]
