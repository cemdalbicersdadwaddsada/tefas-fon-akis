# TEFAS Fon Akış Arşivi

TEFAS'tan her iş günü otomatik olarak tüm fonların **pay adedi + portföy büyüklüğü +
yatırımcı sayısı + fiyat** bilgisini çeker ve `data/snapshot_YYYY-MM-DD.csv` olarak biriktirir.

GitHub Actions üzerinde çalışır — **bilgisayarın açık olması gerekmez.**

## Net para giriş/çıkışı nasıl hesaplanır?
Fon fiyatı yalnız getiriyle değişir; **pay adedi** ise sadece yeni para girince (alım)
artar, para çıkınca (satım) azalır. Yani:

    net_akış (TL) ≈ (payAdet_bugün − payAdet_dün) × fiyat

Biriken snapshot'lardan günlük / haftalık / aylık / 3A / 6A / 1Y momentum çıkarılır.

## Dosyalar
- `fetch_snapshot.py` — TEFAS'tan günün snapshot'ını çeken script
- `.github/workflows/daily.yml` — her iş günü 20:00 (TR) otomatik çalıştıran görev
- `data/` — günlük snapshot CSV'leri burada birikir

## Kurulum (tek seferlik)
1. Bu klasördeki dosyaları GitHub'da yeni bir repo'ya yükle.
2. Repo → **Settings → Actions → General → Workflow permissions** → **Read and write** seç.
3. Repo → **Actions** sekmesi → "TEFAS Gunluk Fon Snapshot" → **Run workflow** ile ilk çalıştır.
4. Sonrası her iş günü otomatik.
