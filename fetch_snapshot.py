# -*- coding: utf-8 -*-
"""
TEFAS günlük fon snapshot toplayıcı.
Her çalıştığında tüm YAT fonlarının o günkü pay adedi / portföy büyüklüğü /
yatırımcı sayısı / fiyatını çeker ve data/snapshot_YYYY-MM-DD.csv olarak yazar.
Zamanla biriken snapshot'lardan net para giriş/çıkışı hesaplanır:
    net_akış ≈ Δ(payAdet) × fiyat
GitHub Actions üzerinde her gün otomatik çalışır — bilgisayar açık olması gerekmez.
"""
import os, sys, csv, datetime, time
import concurrent.futures as cf
import requests

FUND_TYPE = "YAT"           # Menkul kıymet yatırım fonları
OUT_DIR   = "data"
MAX_WORKERS = 6             # TEFAS'ı yormamak için düşük tutuldu
LIMIT = int(os.environ.get("LIMIT", "0"))   # test için; 0 = tümü


def _session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
        "Referer": f"https://www.tefas.gov.tr/tr/fon-getirileri?fundType={FUND_TYPE}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/plain, */*",
    })
    try:
        s.get(f"https://www.tefas.gov.tr/tr/fon-getirileri?fundType={FUND_TYPE}", timeout=30)
    except Exception:
        pass
    return s


def fetch():
    s = _session()
    # 1) Fon listesi + kurucu firma + işlem durumu
    r = s.post("https://www.tefas.gov.tr/api/statistics/tefas/getFplFonList",
               json={"fundType": FUND_TYPE}, timeout=60)
    liste = r.json().get("data") or r.json().get("resultList") or []
    firma, durum, kodlar = {}, {}, []
    for f in liste:
        k = f.get("fonKod") or f.get("fonKodu")
        if k:
            kodlar.append(k)
            firma[k] = f.get("kurucuAd", "")
            durum[k] = f.get("durum", "")
    if LIMIT:
        kodlar = kodlar[:LIMIT]
    print(f"{len(kodlar)} fon listelendi, detaylar çekiliyor...", flush=True)

    # 2) Her fonun anlık pay/büyüklük/yatırımcı/fiyat bilgisi (paralel)
    def detay(kod):
        for _deneme in range(2):
            try:
                rr = s.post("https://www.tefas.gov.tr/api/funds/fonBilgiGetir",
                            json={"fonKodu": kod}, timeout=20)
                d = rr.json().get("resultList", [])
                rec = d[0] if d else None
                if not rec:
                    return None
                return {
                    "fonKodu": kod,
                    "firma": firma.get(kod, ""),
                    "durum": durum.get(kod, ""),
                    "fonKategori": rec.get("fonKategori"),
                    "sonFiyat": rec.get("sonFiyat"),
                    "payAdet": rec.get("payAdet"),
                    "portBuyukluk": rec.get("portBuyukluk"),
                    "yatirimciSayi": rec.get("yatirimciSayi"),
                    "fonUnvan": rec.get("fonUnvan"),
                }
            except Exception:
                time.sleep(1)
        return None

    rows = []
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for r2 in ex.map(detay, kodlar):
            if r2:
                rows.append(r2)
    return rows


def main():
    rows = fetch()
    if not rows:
        print("HATA: TEFAS'tan veri çekilemedi (bot koruması / IP engeli olabilir).",
              file=sys.stderr)
        sys.exit(1)
    today = datetime.date.today().isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"snapshot_{today}.csv")
    cols = ["fonKodu", "firma", "durum", "fonKategori", "sonFiyat",
            "payAdet", "portBuyukluk", "yatirimciSayi", "fonUnvan"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"✓ {len(rows)} fon kaydedildi → {path}", flush=True)


if __name__ == "__main__":
    main()
